from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from typing import Protocol

from app.domain import (
    Category,
    ConfirmationStatus,
    LifecycleStatus,
    ReviewStatus,
    SourceDocument,
    SpendingEvent,
)
from app.services.categorization import MappingRule
from app.services.summary import AnalysisMode


SHEETS_TABS = (
    "raw_imports",
    "normalized_entries",
    "review_queue",
    "mapping_rules",
    "monthly_summary",
)


class SheetsGateway(Protocol):
    def upsert_rows(
        self,
        tab: str,
        rows: list[dict[str, object]],
        key_field: str,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class GoogleSheetsSyncResult:
    normalized_entries: int
    review_queue: int
    mapping_rules: int
    monthly_summary: int


@dataclass(frozen=True, slots=True)
class MonthlySummaryRow:
    month: str
    metric_type: str
    metric_key: str
    metric_value: float


class GoogleSheetsService:
    def __init__(self, gateway: SheetsGateway) -> None:
        self.gateway = gateway

    def sync_all(
        self,
        *,
        repository,
        month: str,
        mode: AnalysisMode = AnalysisMode.FAST,
        exported_at: datetime | None = None,
    ) -> GoogleSheetsSyncResult:
        timestamp = (exported_at or datetime.now(timezone.utc)).isoformat()
        categories = {item.id: item for item in repository.list_categories()}
        events = repository.list_spending_events()

        normalized_rows = self._build_normalized_entry_rows(
            repository=repository,
            events=events,
            categories=categories,
            exported_at=timestamp,
        )
        review_rows = self._build_review_queue_rows(
            events=events,
            categories=categories,
        )
        mapping_rule_rows = self._build_mapping_rule_rows(
            rules=repository.list_mapping_rules(),
            categories=categories,
        )
        summary_rows = self._build_monthly_summary_rows(
            events=events,
            categories=categories,
            mode=mode,
            month=month,
        )

        if normalized_rows:
            self.gateway.upsert_rows("normalized_entries", normalized_rows, "entry_id")
        if review_rows:
            self.gateway.upsert_rows("review_queue", review_rows, "entry_id")
        if mapping_rule_rows:
            self.gateway.upsert_rows("mapping_rules", mapping_rule_rows, "rule_id")
        if summary_rows:
            self.gateway.upsert_rows(
                "monthly_summary",
                [asdict(row) for row in summary_rows],
                "metric_key",
            )

        return GoogleSheetsSyncResult(
            normalized_entries=len(normalized_rows),
            review_queue=len(review_rows),
            mapping_rules=len(mapping_rule_rows),
            monthly_summary=len(summary_rows),
        )

    def _build_normalized_entry_rows(
        self,
        *,
        repository,
        events: list[SpendingEvent],
        categories: dict[str, Category],
        exported_at: str,
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for event in events:
            if not _is_exportable_event(event):
                continue
            source_document = _resolve_source_document(repository, event)
            category_name = _category_name(event, categories)
            rows.append(
                {
                    "entry_id": event.id,
                    "source_type": source_document.source_type.value if source_document else "",
                    "document_id": source_document.id if source_document else "",
                    "merchant_name": event.merchant_normalized,
                    "transaction_date": event.occurred_at.date().isoformat(),
                    "posting_date": event.posted_at.date().isoformat() if event.posted_at else "",
                    "amount": _major_amount(event.amount_minor),
                    "currency": event.currency,
                    "base_currency_amount": "",
                    "suggested_category": category_name,
                    "final_category": category_name,
                    "confidence": 1.0,
                    "duplicate_status": event.lifecycle_status.value,
                    "status": "approved",
                    "review_reasons": ",".join(reason.value for reason in event.review_reasons),
                    "export_timestamp": exported_at,
                }
            )
        return rows

    def _build_review_queue_rows(
        self,
        *,
        events: list[SpendingEvent],
        categories: dict[str, Category],
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for event in events:
            if event.lifecycle_status is not LifecycleStatus.ACTIVE:
                continue
            if event.review_status is not ReviewStatus.NEEDS_REVIEW:
                continue
            rows.append(
                {
                    "entry_id": event.id,
                    "issue_type": _review_issue_type(event),
                    "merchant": event.merchant_normalized,
                    "amount": _major_amount(event.amount_minor),
                    "currency": event.currency,
                    "suggested_category": _category_name(event, categories),
                    "rationale": _review_rationale(event),
                    "duplicate_signals": "marked_duplicate" if event.lifecycle_status is LifecycleStatus.DUPLICATE else "",
                    "reviewer_status": event.review_status.value,
                }
            )
        return rows

    def _build_mapping_rule_rows(
        self,
        *,
        rules: list[MappingRule],
        categories: dict[str, Category],
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for rule in rules:
            rows.append(
                {
                    "rule_id": rule.id,
                    "field": rule.pattern_type.value,
                    "pattern": rule.pattern,
                    "target_category": categories.get(rule.category_id, Category(rule.category_id, rule.category_id, datetime.now(timezone.utc))).name,
                    "priority": rule.priority,
                    "created_by": "user" if rule.created_from_review else "system",
                    "created_at": rule.created_at.isoformat() if rule.created_at else "",
                }
            )
        return rows

    def _build_monthly_summary_rows(
        self,
        *,
        events: list[SpendingEvent],
        categories: dict[str, Category],
        mode: AnalysisMode,
        month: str,
    ) -> list[MonthlySummaryRow]:
        approved = [event for event in events if _is_summary_included(event, mode=mode, month=month)]
        by_category: dict[str, float] = {}
        by_merchant: dict[str, float] = {}
        by_currency: dict[str, float] = {}
        uncategorized_count = 0

        for event in approved:
            category_name = _category_name(event, categories)
            merchant_name = event.merchant_normalized or "unknown_merchant"
            amount = _major_amount(event.amount_minor)

            by_category[f"{month}:{category_name}"] = by_category.get(f"{month}:{category_name}", 0) + amount
            by_merchant[f"{month}:{merchant_name}"] = by_merchant.get(f"{month}:{merchant_name}", 0) + amount
            by_currency[f"{month}:{event.currency}"] = by_currency.get(f"{month}:{event.currency}", 0) + amount
            if category_name == "uncategorized":
                uncategorized_count += 1

        rows: list[MonthlySummaryRow] = []
        for key, value in by_category.items():
            rows.append(MonthlySummaryRow(month=month, metric_type="category_total", metric_key=key, metric_value=value))
        for key, value in by_merchant.items():
            rows.append(MonthlySummaryRow(month=month, metric_type="merchant_total", metric_key=key, metric_value=value))
        for key, value in by_currency.items():
            rows.append(MonthlySummaryRow(month=month, metric_type="currency_total", metric_key=key, metric_value=value))
        if uncategorized_count:
            rows.append(
                MonthlySummaryRow(
                    month=month,
                    metric_type="uncategorized_count",
                    metric_key=f"{month}:uncategorized_count",
                    metric_value=float(uncategorized_count),
                )
            )
        return rows


class GoogleSheetsGateway:
    def __init__(self, *, spreadsheet_id: str, service_account_json: str) -> None:
        self.spreadsheet_id = spreadsheet_id
        self._service_account_json = service_account_json
        self._sheets_api = None

    def upsert_rows(self, tab: str, rows: list[dict[str, object]], key_field: str) -> None:
        if not rows:
            return
        sheets_api = self._get_sheets_api()
        existing_values = self._get_existing_values(sheets_api=sheets_api, tab=tab)
        columns = _merge_columns(existing_values[0] if existing_values else [], rows)
        if key_field not in columns:
            raise ValueError(f"sheet tab {tab} is missing required key field {key_field}")

        self._update_headers(sheets_api=sheets_api, tab=tab, columns=columns)
        key_index = columns.index(key_field)
        existing_by_key = self._existing_row_numbers(existing_values, key_index=key_index)

        updates = []
        appends = []
        for row in rows:
            key = _to_string_value(row.get(key_field)).strip()
            if not key:
                continue
            values = [_to_string_value(row.get(column)) for column in columns]
            existing_row = existing_by_key.get(key)
            if existing_row:
                updates.append(
                    {
                        "range": f"{tab}!A{existing_row}:{_a1_column(len(columns) - 1)}{existing_row}",
                        "values": [values],
                    }
                )
            else:
                appends.append(values)

        if updates:
            sheets_api.spreadsheets().values().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body={"valueInputOption": "RAW", "data": updates},
            ).execute()
        if appends:
            sheets_api.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{tab}!A:{_a1_column(len(columns) - 1)}",
                valueInputOption="RAW",
                body={"values": appends},
            ).execute()

    def _get_sheets_api(self):
        if self._sheets_api is None:
            credentials = _parse_service_account(self._service_account_json)
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            auth = Credentials.from_service_account_info(
                credentials,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )
            self._sheets_api = build("sheets", "v4", credentials=auth)
        return self._sheets_api

    def _get_existing_values(self, *, sheets_api, tab: str) -> list[list[str]]:
        response = (
            sheets_api.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range=f"{tab}!A:ZZ")
            .execute()
        )
        values = response.get("values", [])
        return [[str(cell) for cell in row] for row in values]

    def _update_headers(self, *, sheets_api, tab: str, columns: list[str]) -> None:
        (
            sheets_api.spreadsheets()
            .values()
            .update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{tab}!A1:{_a1_column(len(columns) - 1)}1",
                valueInputOption="RAW",
                body={"values": [columns]},
            )
            .execute()
        )

    def _existing_row_numbers(self, existing_values: list[list[str]], *, key_index: int) -> dict[str, int]:
        existing: dict[str, int] = {}
        for index, row in enumerate(existing_values[1:], start=2):
            key = str(row[key_index]).strip() if key_index < len(row) else ""
            if key:
                existing[key] = index
        return existing


def build_google_sheets_gateway_from_env(env: Mapping[str, str | None]) -> GoogleSheetsGateway | None:
    if not should_use_google_sheets_gateway(env):
        return None
    return GoogleSheetsGateway(
        spreadsheet_id=(env.get("GOOGLE_SHEETS_SPREADSHEET_ID") or "").strip(),
        service_account_json=(env.get("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON") or "").strip(),
    )


def should_use_google_sheets_gateway(env: Mapping[str, str | None]) -> bool:
    return (
        (env.get("GOOGLE_SHEETS_ENABLED") or "").strip().lower() == "true"
        and bool((env.get("GOOGLE_SHEETS_SPREADSHEET_ID") or "").strip())
        and bool((env.get("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON") or "").strip())
    )


def _resolve_source_document(repository, event: SpendingEvent) -> SourceDocument | None:
    if event.canonical_source_evidence_id is None:
        return None
    evidence = repository.get_evidence_record(event.canonical_source_evidence_id)
    if evidence is None:
        return None
    return repository.get_source_document(evidence.source_document_id)


def _is_exportable_event(event: SpendingEvent) -> bool:
    return (
        event.lifecycle_status is LifecycleStatus.ACTIVE
        and event.review_status is not ReviewStatus.NEEDS_REVIEW
        and event.confirmation_status in {ConfirmationStatus.CONFIRMED, ConfirmationStatus.MANUAL_CONFIRMED}
    )


def _is_summary_included(event: SpendingEvent, *, mode: AnalysisMode, month: str) -> bool:
    if event.occurred_at.strftime("%Y-%m") != month:
        return False
    if not _is_exportable_event(event):
        return False
    if mode is AnalysisMode.FAST:
        return True
    return event.confirmation_status in {ConfirmationStatus.CONFIRMED, ConfirmationStatus.MANUAL_CONFIRMED}


def _category_name(event: SpendingEvent, categories: dict[str, Category]) -> str:
    if not event.category_id:
        return "uncategorized"
    return categories.get(event.category_id, Category(event.category_id, event.category_id, datetime.now(timezone.utc))).name


def _review_issue_type(event: SpendingEvent) -> str:
    if event.review_reasons:
        return event.review_reasons[0].value
    if event.lifecycle_status is LifecycleStatus.DUPLICATE:
        return "possible_duplicate"
    if event.confirmation_status is ConfirmationStatus.PROVISIONAL:
        return "unmatched_receipt"
    return "needs_review"


def _review_rationale(event: SpendingEvent) -> str:
    if event.review_reasons:
        return ", ".join(reason.value for reason in event.review_reasons)
    if event.confirmation_status is ConfirmationStatus.PROVISIONAL:
        return "receipt is still provisional and needs statement or manual confirmation"
    return f"event requires operator review with source_quality={event.source_quality.value}"


def _major_amount(amount_minor: int) -> float:
    return round(amount_minor / 100, 2)


def _parse_service_account(value: str) -> dict[str, str]:
    trimmed = value.strip()
    parsed = json.loads(trimmed)
    email = parsed.get("client_email")
    key = parsed.get("private_key")
    if not email or not key:
        raise ValueError("invalid GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON, missing client_email or private_key")
    parsed["private_key"] = str(key).replace("\\n", "\n")
    return parsed


def _merge_columns(existing: list[str], incoming_rows: list[dict[str, object]]) -> list[str]:
    seen = set(existing)
    merged = list(existing)
    for row in incoming_rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                merged.append(key)
    return merged


def _to_string_value(value: object | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _a1_column(index: int) -> str:
    value = index + 1
    column = ""
    while value > 0:
        remainder = (value - 1) % 26
        column = chr(65 + remainder) + column
        value = (value - 1) // 26
    return column
