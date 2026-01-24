from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReceiptTextImportRequest(BaseModel):
    raw_text: str = Field(min_length=1)
    filename: str | None = None

    @field_validator("raw_text")
    @classmethod
    def normalize_raw_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("raw_text is required")
        return normalized


class StatementCsvImportRequest(BaseModel):
    raw_csv: str = Field(min_length=1)
    filename: str | None = None

    @field_validator("raw_csv")
    @classmethod
    def normalize_raw_csv(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("raw_csv is required")
        return normalized


class ImportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_document_id: str
    evidence_record_ids: list[str]
    spending_event_ids: list[str]
    evidence_link_ids: list[str]
    match_candidate_ids: list[str] = []
