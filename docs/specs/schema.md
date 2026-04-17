# Canonical Schema Spec (V1)

## Purpose

Define the single internal transaction contract used across receipts, bank statements, and credit card statements.

## Core Entity

`NormalizedEntry` is the canonical record. All ingestion adapters must map into this schema before any export.

Required fields:

- `entryId`
- `sourceDocument.documentId`
- `sourceDocument.sourceType`
- `amount`
- `currency`
- `categoryDecision.suggestedCategory`
- `duplicateCheck.status`
- `status`
- `extractionMeta.confidence`
- `createdAt`
- `updatedAt`

Important optional fields:

- `merchantRaw`
- `merchantNormalized`
- `description`
- `reference`
- `transactionDate`
- `postingDate`
- `taxAmount`
- `lineItems`
- `categoryDecision.finalCategory`
- `duplicateCheck.relatedEntryId`

## Status and Review Contract

`status` values:

- `normalized`: valid but pending approval
- `needs_review`: uncertain, blocked, or suspicious
- `approved`: explicitly approved or auto-approved by low-risk rule

`reviewReasons` values include:

- `missing_amount`
- `missing_currency`
- `missing_transaction_date`
- `low_extraction_confidence`
- `uncertain_category`
- `duplicate_suspected`
- `exact_duplicate_import`
- `parse_error`
- `ambiguous_match`

## Duplicate Contract

`duplicateCheck.status` values:

- `none`
- `exact_duplicate_import`
- `near_duplicate_suspected`
- `recurring_candidate`

Rules:

- `exact_duplicate_import` must not be exported as a new active approved row
- `near_duplicate_suspected` must route to review in V1
- `recurring_candidate` remains active by default and is used for summary signals

## Invariants

- Every `NormalizedEntry` must link back to a `SourceDocumentRef`.
- Raw and normalized fields must both be preservable for audits.
- Deterministic policy owns status transitions.
- LLM outputs are suggestions only and must not bypass schema validation.
