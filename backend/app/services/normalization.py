from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re


class NormalizationError(ValueError):
    pass


_CURRENCY_SYMBOLS = {
    "€": "EUR",
    "$": "USD",
    "£": "GBP",
}


def normalize_currency(value: str | None, *, default: str = "EUR") -> str:
    if value is None:
        return default
    cleaned = value.strip().upper()
    if not cleaned:
        return default
    return _CURRENCY_SYMBOLS.get(cleaned, cleaned)


def parse_amount_minor(value: str) -> int:
    cleaned = value.strip()
    if not cleaned:
        raise NormalizationError("amount is required")

    is_negative = cleaned.startswith("-") or cleaned.endswith("-")
    cleaned = cleaned.replace(" ", "")
    cleaned = re.sub(r"[^0-9,.-]", "", cleaned)
    cleaned = cleaned.strip("-")

    if "," in cleaned and "." in cleaned:
        decimal_separator = "," if cleaned.rfind(",") > cleaned.rfind(".") else "."
    elif "," in cleaned:
        decimal_separator = ","
    else:
        decimal_separator = "."

    if decimal_separator == ",":
        cleaned = cleaned.replace(".", "")
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")

    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise NormalizationError(f"invalid amount: {value}") from exc

    minor = int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -minor if is_negative else minor


def parse_datetime(value: str) -> datetime:
    cleaned = value.strip()
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(cleaned, pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise NormalizationError(f"invalid date: {value}")


def normalize_merchant(value: str) -> str:
    cleaned = " ".join(value.strip().split())
    if not cleaned:
        raise NormalizationError("merchant is required")
    return cleaned.title()
