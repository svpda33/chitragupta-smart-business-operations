"""Date and time sources. Services import from here so there is a single place for 'today'."""

from datetime import date, datetime, timezone


def today() -> date:
    return date.today()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
