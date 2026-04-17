export const SOURCE_TYPES = [
  "receipt",
  "bank_statement",
  "credit_card_statement"
] as const;
export type SourceType = (typeof SOURCE_TYPES)[number];

export const CATEGORY_VALUES = [
  "groceries",
  "transport",
  "dining",
  "shopping",
  "utilities",
  "housing",
  "health",
  "travel",
  "subscriptions",
  "fees",
  "transfer",
  "income",
  "uncategorized"
] as const;
export type Category = (typeof CATEGORY_VALUES)[number];

export const SUGGESTION_SOURCES = ["rule", "llm", "user", "mixed"] as const;
export type SuggestionSource = (typeof SUGGESTION_SOURCES)[number];

export const DUPLICATE_STATUSES = [
  "none",
  "exact_duplicate_import",
  "near_duplicate_suspected",
  "recurring_candidate"
] as const;
export type DuplicateStatus = (typeof DUPLICATE_STATUSES)[number];

export const ENTRY_STATUSES = ["normalized", "needs_review", "approved"] as const;
export type EntryStatus = (typeof ENTRY_STATUSES)[number];

export const REVIEW_REASONS = [
  "missing_amount",
  "missing_currency",
  "missing_transaction_date",
  "low_extraction_confidence",
  "uncertain_category",
  "duplicate_suspected",
  "exact_duplicate_import",
  "parse_error",
  "ambiguous_match"
] as const;
export type ReviewReason = (typeof REVIEW_REASONS)[number];

export const AUDIT_EVENT_TYPES = [
  "import_created",
  "extraction_completed",
  "entry_normalized",
  "category_suggested",
  "duplicate_checked",
  "review_routed",
  "entry_approved",
  "entry_rejected",
  "entry_exported"
] as const;
export type AuditEventType = (typeof AUDIT_EVENT_TYPES)[number];
