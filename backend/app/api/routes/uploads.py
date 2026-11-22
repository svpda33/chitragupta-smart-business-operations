"""Secure, business-scoped image upload endpoints for business logos and product photos."""

import os
from pathlib import Path
import re
import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_business
from app.core.errors import AppError
from app.database.session import get_db
from app.models.business import Business
from app.services import inventory_service

router = APIRouter(prefix="/uploads", tags=["uploads"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
}
SAFE_FILENAME_RE = re.compile(r"^[a-f0-9]{32}\.(png|jpg|webp)$")
UPLOADS_ROOT = Path(__file__).resolve().parents[3] / "instance" / "uploads"


def _detect_image_ext(content: bytes, content_type: str | None) -> str:
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if content.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return "webp"
    if content_type in ALLOWED_TYPES:
        raise AppError(422, "Uploaded file content does not match a valid PNG, JPEG, or WebP image.")
    raise AppError(422, "Only PNG, JPEG, and WebP images are supported.")


async def _save_validated_image(business_id: int, file: UploadFile) -> str:
    content = await file.read()
    if not content:
        raise AppError(422, "Uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise AppError(422, "Image must be 5 MB or smaller.")

    ext = _detect_image_ext(content, file.content_type)
    biz_dir = UPLOADS_ROOT / f"business_{business_id}"
    biz_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}.{ext}"
    target = biz_dir / filename
    target.write_bytes(content)
    return f"/api/uploads/{business_id}/{filename}"


def _delete_local_file(url: str | None, business_id: int) -> None:
    if not url:
        return
    prefix = f"/api/uploads/{business_id}/"
    if not url.startswith(prefix):
        return
    filename = url[len(prefix):]
    if not SAFE_FILENAME_RE.fullmatch(filename):
        return
    target = UPLOADS_ROOT / f"business_{business_id}" / filename
    if target.is_file():
        try:
            os.remove(target)
        except OSError:
            pass


@router.post("/business-logo")
async def upload_business_logo(
    file: UploadFile = File(...),
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    old_url = biz.logo_url
    new_url = await _save_validated_image(biz.id, file)
    biz.logo_url = new_url
    db.commit()
    db.refresh(biz)
    _delete_local_file(old_url, biz.id)
    return {"logo_url": new_url}


@router.delete("/business-logo")
def remove_business_logo(
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    old_url = biz.logo_url
    biz.logo_url = None
    db.commit()
    _delete_local_file(old_url, biz.id)
    return {"logo_url": None}


@router.post("/products/{product_id}")
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    product = inventory_service.get_product_entity(db, biz.id, product_id)
    old_url = product.image_url
    new_url = await _save_validated_image(biz.id, file)
    product.image_url = new_url
    db.commit()
    db.refresh(product)
    _delete_local_file(old_url, biz.id)
    return {"image_url": new_url}


@router.delete("/products/{product_id}")
def remove_product_image(
    product_id: int,
    biz: Business = Depends(get_current_business),
    db: Session = Depends(get_db),
) -> dict:
    product = inventory_service.get_product_entity(db, biz.id, product_id)
    old_url = product.image_url
    product.image_url = None
    db.commit()
    _delete_local_file(old_url, biz.id)
    return {"image_url": None}


@router.get("/{business_id}/{filename}")
def get_uploaded_file(
    business_id: int,
    filename: str,
    biz: Business = Depends(get_current_business),
):
    if biz.id != business_id:
        raise AppError(403, "You do not have access to this business's files.")
    if not SAFE_FILENAME_RE.fullmatch(filename):
        raise AppError(404, "File not found.")
    target = UPLOADS_ROOT / f"business_{business_id}" / filename
    if not target.is_file():
        raise AppError(404, "File not found.")
    return FileResponse(target)
