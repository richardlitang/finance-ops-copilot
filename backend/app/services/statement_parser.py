from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO

from .normalization import (
    NormalizationError,
    normalize_currency,
    normalize_merchant,
    parse_amount_minor,
    parse_datetime,
)


@dataclass(frozen=True, slots=True)
class ParsedStatementRow:
    row_index: int
    occurred_at: object
    posted_at: object | None
    description_raw: str
    merchant_raw: str
    merchant_normalized: str
    amount_minor: int
    currency: str
    warnings: tuple[str, ...]


class StatementParseError(ValueError):
    pass


def parse_statement_csv(raw_csv: str) -> list[ParsedStatementRow]:
    reader = csv.DictReader(StringIO(raw_csv.strip()))
    required = {"date", "description", "amount"}
    fieldnames = {name.strip().lower() for name in (reader.fieldnames or [])}
    missing = required - fieldnames
    if missing:
        raise StatementParseError(f"missing statement columns: {', '.join(sorted(missing))}")

    parsed: list[ParsedStatementRow] = []
    for index, row in enumerate(reader, start=1):
        normalized_row = {key.strip().lower(): value for key, value in row.items() if key is not None}
        description = (normalized_row.get("description") or "").strip()
        merchant_raw = (normalized_row.get("merchant") or description).strip()
        posted_raw = (normalized_row.get("posted_date") or "").strip()
        warnings: list[str] = []
        posted_at = _parse_row_date(posted_raw, row_index=index, column="posted_date") if posted_raw else None

        if not merchant_raw:
            warnings.append("missing_merchant")
            merchant_raw = "Unknown Merchant"

        parsed.append(
            ParsedStatementRow(
                row_index=index,
                occurred_at=_parse_row_date(normalized_row["date"], row_index=index, column="date"),
                posted_at=posted_at,
                description_raw=description,
                merchant_raw=merchant_raw,
                merchant_normalized=normalize_merchant(merchant_raw),
                amount_minor=_parse_row_amount(normalized_row["amount"], row_index=index),
                currency=normalize_currency(normalized_row.get("currency")),
                warnings=tuple(warnings),
            )
        )
    return parsed


def _parse_row_amount(value: str, *, row_index: int) -> int:
    try:
        return parse_amount_minor(value)
    except NormalizationError as exc:
        raise StatementParseError(
            f"invalid statement row {row_index} column amount: {exc}"
        ) from exc


def _parse_row_date(value: str, *, row_index: int, column: str):
    try:
        return parse_datetime(value)
    except NormalizationError as exc:
        raise StatementParseError(
            f"invalid statement row {row_index} column {column}: {exc}"
        ) from exc
