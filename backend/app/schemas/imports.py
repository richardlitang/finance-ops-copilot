from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ReceiptTextImportRequest(BaseModel):
    raw_text: str
    filename: str | None = None


class StatementCsvImportRequest(BaseModel):
    raw_csv: str
    filename: str | None = None


class ImportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_document_id: str
    evidence_record_ids: list[str]
    spending_event_ids: list[str]
    evidence_link_ids: list[str]
    match_candidate_ids: list[str] = []

