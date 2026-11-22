"""Money helpers. Money is stored as integer paise; users enter rupees (at most 2 decimals)."""

import re
from decimal import Decimal, InvalidOperation

_RUPEES_PATTERN = re.compile(r"-?\d+(\.\d{1,2})?")
_RUPEES_MESSAGE = "Enter an amount in rupees with at most 2 decimal places, for example 1250.50."


def rupees_to_paise(value) -> int:
    """Convert a rupee value (int, Decimal, float, or str) to integer paise exactly."""
    if isinstance(value, bool):
        raise ValueError(_RUPEES_MESSAGE)
    if isinstance(value, int):
        text = str(value)
    elif isinstance(value, Decimal):
        text = format(value, "f")
    elif isinstance(value, float):
        text = str(value)
    elif isinstance(value, str):
        text = value
    else:
        raise ValueError(_RUPEES_MESSAGE)

    text = text.strip()
    if not _RUPEES_PATTERN.fullmatch(text):
        raise ValueError(_RUPEES_MESSAGE)
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(_RUPEES_MESSAGE) from exc
    if amount.as_tuple().exponent < -2:
        raise ValueError(_RUPEES_MESSAGE)
    return int((amount * 100).to_integral_value())


def positive_rupees_to_paise(value) -> int:
    """Same as rupees_to_paise but rejects zero and negative amounts."""
    paise = rupees_to_paise(value)
    if paise <= 0:
        raise ValueError("Enter an amount greater than zero.")
    return paise


def paise_to_rupees_text(paise: int) -> str:
    """Format paise as rupees with thousands separators and two decimals, e.g. 1234.5 -> '1,234.50'."""
    sign = "-" if paise < 0 else ""
    rupees, cents = divmod(abs(int(paise)), 100)
    return f"{sign}{rupees:,}.{cents:02d}"
