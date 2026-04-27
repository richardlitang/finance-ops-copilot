from __future__ import annotations

from dataclasses import dataclass
import re

from .normalization import NormalizationError, normalize_currency, normalize_merchant, parse_amount_minor, parse_datetime


@dataclass(frozen=True, slots=True)
class ParsedReceipt:
    merchant_raw: str | None
    merchant_normalized: str | None
    occurred_at: object | None
    amount_minor: int | None
    currency: str
    confidence: float
    warnings: tuple[str, ...]


_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})\b")
_TOTAL_RE = re.compile(
    r"\b(?:total|amount due|paid|grand total)\b[^0-9€$£-]*([€$£]?\s*-?\d[\d\s.,]*)(?:\s*(EUR|USD|GBP))?",
    re.IGNORECASE,
)
_CURRENCY_RE = re.compile(r"(EUR|USD|GBP|€|\$|£)", re.IGNORECASE)


def parse_receipt_text(raw_text: str) -> ParsedReceipt:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    warnings: list[str] = []

    merchant_raw = lines[0] if lines else None
    merchant_normalized = None
    if merchant_raw is None:
        warnings.append("missing_merchant")
    else:
        try:
            merchant_normalized = normalize_merchant(merchant_raw)
        except NormalizationError:
            warnings.append("missing_merchant")

    occurred_at = None
    date_match = _DATE_RE.search(raw_text)
    if date_match is None:
        warnings.append("missing_date")
    else:
        try:
            occurred_at = parse_datetime(date_match.group(1))
        except NormalizationError:
            warnings.append("invalid_date")

    amount_minor = None
    total_match = _TOTAL_RE.search(raw_text)
    if total_match is None:
        warnings.append("missing_total")
    else:
        try:
            amount_minor = parse_amount_minor(total_match.group(1))
        except NormalizationError:
            warnings.append("invalid_total")

    currency_match = _CURRENCY_RE.search(raw_text)
    currency = normalize_currency(currency_match.group(1) if currency_match else None)

    complete_fields = sum(
        value is not None for value in (merchant_normalized, occurred_at, amount_minor, currency)
    )
    confidence = complete_fields / 4
    if warnings:
        confidence = min(confidence, 0.74)

    return ParsedReceipt(
        merchant_raw=merchant_raw,
        merchant_normalized=merchant_normalized,
        occurred_at=occurred_at,
        amount_minor=amount_minor,
        currency=currency,
        confidence=confidence,
        warnings=tuple(warnings),
    )
