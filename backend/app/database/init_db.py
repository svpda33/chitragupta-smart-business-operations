"""Table creation and safe idempotent schema migration helper."""

from sqlalchemy import inspect, text

import app.models  # noqa: F401  (registers model metadata)
from app.database.session import Base, engine

_SAFE_COLUMN_ADDITIONS: list[tuple[str, str, str]] = [
    ("customers", "business_id", "INTEGER"),
    ("invoices", "business_id", "INTEGER"),
    ("invoice_items", "product_id", "INTEGER"),
    ("payments", "business_id", "INTEGER"),
    ("expenses", "business_id", "INTEGER"),
    ("settings", "business_id", "INTEGER"),
    ("ai_conversations", "business_id", "INTEGER"),
]


def _apply_safe_migrations(bind_engine) -> None:
    """Safely add newly introduced nullable columns to pre-existing SQLite tables without dropping data."""
    inspector = inspect(bind_engine)
    existing_tables = set(inspector.get_table_names())
    with bind_engine.begin() as conn:
        for table_name, col_name, col_type in _SAFE_COLUMN_ADDITIONS:
            if table_name not in existing_tables:
                continue
            existing_cols = {c["name"] for c in inspector.get_columns(table_name)}
            if col_name not in existing_cols:
                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"))


def create_all_tables(bind_engine=None) -> None:
    target = bind_engine or engine
    Base.metadata.create_all(bind=target)
    _apply_safe_migrations(target)
