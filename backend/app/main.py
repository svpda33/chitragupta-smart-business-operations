from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import AppError
from app.database.init_db import create_all_tables

settings = get_settings()

VALIDATION_DETAIL = "Please correct the highlighted fields."
UNEXPECTED_DETAIL = "An unexpected error occurred."
LOCATION_PREFIXES = ("body", "query", "path", "header")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_all_tables()
    yield


app = FastAPI(title="Chitragupta API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


def _field_path(location) -> str:
    parts = [str(part) for part in location if str(part) not in LOCATION_PREFIXES]
    return ".".join(parts)


def _clean_message(message: str) -> str:
    prefix = "Value error, "
    return message[len(prefix):] if message.startswith(prefix) else message


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {"field": _field_path(error["loc"]), "message": _clean_message(error["msg"])}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": VALIDATION_DETAIL, "errors": errors})


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    content: dict = {"detail": exc.detail}
    if exc.field:
        content["errors"] = [{"field": exc.field, "message": exc.detail}]
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def unexpected_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": UNEXPECTED_DETAIL})
