from __future__ import annotations

from hashlib import sha256
from typing import Mapping


FingerprintValue = str | int | None


def _normalize_part(value: FingerprintValue) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def _stable_hash(parts: list[FingerprintValue]) -> str:
    stable = "|".join(_normalize_part(part) for part in parts)
    return sha256(stable.encode("utf-8")).hexdigest()


def build_source_document_fingerprint(
    *,
    source_type: str,
    raw_text: str | None = None,
    filename: str | None = None,
) -> str:
    return _stable_hash([source_type, raw_text, filename])


def build_evidence_fingerprint(
    *,
    source_document_id: str,
    evidence_type: str,
    fields: Mapping[str, FingerprintValue],
) -> str:
    ordered_field_parts: list[FingerprintValue] = []
    for key in sorted(fields):
        ordered_field_parts.append(key)
        ordered_field_parts.append(fields[key])
    return _stable_hash([source_document_id, evidence_type, *ordered_field_parts])
