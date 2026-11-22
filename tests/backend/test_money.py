from decimal import Decimal

import pytest

from app.utils.money import paise_to_rupees_text, positive_rupees_to_paise, rupees_to_paise


@pytest.mark.parametrize(
    "value, expected",
    [
        ("1000.00", 100000),
        ("250.5", 25050),
        ("250.50", 25050),
        (1000, 100000),
        (Decimal("12.34"), 1234),
        (1.5, 150),
        (" 99 ", 9900),
        ("0.05", 5),
        ("-5", -500),
    ],
)
def test_rupees_to_paise_exact(value, expected):
    assert rupees_to_paise(value) == expected


@pytest.mark.parametrize("value", ["1.005", "abc", "", "1,000", "1e3", "12.345"])
def test_rupees_to_paise_rejects_invalid(value):
    with pytest.raises(ValueError):
        rupees_to_paise(value)


def test_positive_rejects_zero_and_negative():
    with pytest.raises(ValueError):
        positive_rupees_to_paise("0")
    with pytest.raises(ValueError):
        positive_rupees_to_paise("-1.00")
    assert positive_rupees_to_paise("0.01") == 1


@pytest.mark.parametrize(
    "paise, expected",
    [
        (123450, "1,234.50"),
        (5, "0.05"),
        (100000000, "1,000,000.00"),
        (-250, "-2.50"),
        (0, "0.00"),
    ],
)
def test_paise_to_rupees_text(paise, expected):
    assert paise_to_rupees_text(paise) == expected
