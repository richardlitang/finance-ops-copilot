from enum import StrEnum


class SourceType(StrEnum):
    RECEIPT_TEXT = "receipt_text"
    RECEIPT_IMAGE = "receipt_image"
    BANK_CSV = "bank_csv"
    CARD_CSV = "card_csv"
    MANUAL = "manual"


class SourceDocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    FAILED = "failed"


class EvidenceType(StrEnum):
    RECEIPT = "receipt"
    STATEMENT_ROW = "statement_row"
    MANUAL_ENTRY = "manual_entry"


class Direction(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"
    TRANSFER = "transfer"


class ConfirmationStatus(StrEnum):
    PROVISIONAL = "provisional"
    CONFIRMED = "confirmed"
    MANUAL_CONFIRMED = "manual_confirmed"


class ReviewStatus(StrEnum):
    CLEAR = "clear"
    NEEDS_REVIEW = "needs_review"
    RESOLVED = "resolved"


class ReviewReason(StrEnum):
    UNCERTAIN_CATEGORY = "uncertain_category"
    POSSIBLE_DUPLICATE = "possible_duplicate"
    POSSIBLE_RECEIPT_STATEMENT_MATCH = "possible_receipt_statement_match"
    AMOUNT_MISMATCH = "amount_mismatch"
    UNMATCHED_RECEIPT = "unmatched_receipt"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    PARSE_WARNING = "parse_warning"


class LifecycleStatus(StrEnum):
    ACTIVE = "active"
    DUPLICATE = "duplicate"
    IGNORED = "ignored"


class SourceQuality(StrEnum):
    RECEIPT_ONLY = "receipt_only"
    STATEMENT_ONLY = "statement_only"
    RECEIPT_AND_STATEMENT = "receipt_and_statement"
    MANUAL = "manual"


class EvidenceLinkType(StrEnum):
    CREATED_FROM = "created_from"
    MATCHED_TO = "matched_to"
    SUPPORTING_RECEIPT = "supporting_receipt"
    STATEMENT_CONFIRMATION = "statement_confirmation"


class EvidenceLinkStatus(StrEnum):
    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class AuditActor(StrEnum):
    SYSTEM = "system"
    USER = "user"


class AuditEventType(StrEnum):
    IMPORT_CREATED = "import_created"
    REVIEW_ROUTED = "review_routed"
    MATCH_CONFIRMED = "match_confirmed"
    MATCH_REJECTED = "match_rejected"
    CATEGORY_CORRECTED = "category_corrected"
    MAPPING_RULE_CREATED = "mapping_rule_created"
    EVENT_MANUAL_CONFIRMED = "event_manual_confirmed"
    EVENT_MARKED_DUPLICATE = "event_marked_duplicate"
    EVENT_IGNORED = "event_ignored"
    GOOGLE_SHEETS_EXPORTED = "google_sheets_exported"
