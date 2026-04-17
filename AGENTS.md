# Finance Ops Copilot (Agent Operating Guide)

Local-first financial document normalization pipeline for receipts, bank statements, and credit card statements. This repo turns messy financial inputs into reviewable, auditable, spreadsheet-ready entries.

Use this file as the operating contract for AI coding agents working in this repository.

## Core Objective

Prioritize in this order:

1. Correctness of normalized financial data
2. Auditability and user trust
3. Deterministic review and duplicate safety
4. Privacy-aware local-first behavior
5. Maintainability and simplicity
6. Delivery speed

Prefer explicit, schema-first, testable code over clever pipelines or agentic complexity.

## Product Wedge (Do Not Dilute)

This product is not a chatbot and not a full bookkeeping suite.

Protect these differentiators:

- one canonical internal entry model across all source types
- deterministic validation, duplicate handling, and status transitions
- human review for uncertainty instead of silent auto-approval
- strong provenance from source document to exported row
- Google Sheets as a review/export surface, not the source of truth
- narrow, bounded LLM assistance instead of open-ended automation

## Non-Negotiable Rules

- Do not bypass review when extraction, categorization, matching, or duplicate confidence is weak.
- Do not let LLM output directly own status transitions, arithmetic, dedupe decisions, or side effects.
- Do not put source-specific parsing rules directly into shared normalization logic.
- Do not lose raw provenance, extraction warnings, or audit history during transforms.
- Do not silently merge near-duplicates in V1.
- Do not treat Google Sheets as the canonical database.
- Do not send raw documents or extracted text off-device unless the task explicitly requires it.
- Do not add new dependencies unless explicitly requested or clearly justified.
- If tests, typecheck, or build are not run, state that explicitly.
- For all writing in this repository, do not use em dashes. Use commas, periods, or parentheses instead.
- When remaining context is 30% or lower, run `/compact` before continuing substantial work.

## Agent-First Harness Engineering Rules

Apply these rules to keep agent throughput high without quality drift.

- Keep `AGENTS.md` short and navigational, not encyclopedic. Put durable detail in versioned docs.
- Treat repository artifacts as source of truth. If guidance lives in chat or memory, move it into repo docs.
- Use progressive disclosure for context. Start from index docs, then follow links to specific domains.
- Treat plans as first-class artifacts. Keep active/completed execution plans and technical debt logs in-repo.
- Enforce architecture and style mechanically through linters, structural tests, and CI, not prompt-only reminders.
- Encode recurring review feedback into rules, checks, or scripts so the same issue is auto-prevented next time.
- Prefer strict boundaries with local implementation freedom. Enforce dependency direction, not stylistic micromanagement.
- Keep PRs small and short-lived. Favor fast correction loops over long-lived blocked branches when risk is controlled.
- Run recurring cleanup passes for drift and duplication. Open small targeted fix PRs instead of periodic large rewrites.

## Architecture Boundaries

Keep responsibilities clean:

- ingestion: import files/text, assign document IDs, capture metadata
- classification: determine source type using explicit hints and heuristics first
- adapters: parse source-specific input into candidate fields
- normalization: convert candidates into the canonical schema
- duplicate engine: import fingerprints, exact dedupe, near-duplicate scoring
- categorization engine: mapping rules first, heuristic or LLM fallback second
- validation and review router: compute status and review reasons
- sync layer: export approved entries to Google Sheets
- audit layer: record extraction, normalization, review, and export events

If logic is reused or non-trivial, it belongs in a domain module, not in UI, route handlers, or one-off scripts.

## Canonical Data Contract

The canonical model is the product. Protect it.

Required core entities:

- `NormalizedEntry`
- `SourceDocumentRef`
- `ExtractionMeta`
- `CategoryDecision`
- `DuplicateCheckResult`
- `MappingRule`
- `AuditEvent`

Required invariants:

- every exportable row maps back to a source document or source row
- raw values and normalized values can be inspected side by side when relevant
- confidence, warnings, and review reasons are preserved, not overwritten
- stable internal IDs survive review and export flows
- exact duplicate imports do not create a second active exportable row

## LLM Boundary Contract

Allowed uses:

- ambiguous source classification fallback
- messy receipt extraction fallback
- merchant normalization suggestions
- category suggestion after rules fail
- review explanation text

Not allowed:

- CSV parsing ownership
- date or currency normalization ownership
- amount math or arithmetic checks
- import fingerprint generation
- exact duplicate decisions
- near-duplicate merge decisions
- approval state transitions
- Google Sheets writes
- audit log authorship as the sole record

LLM outputs must be treated as suggestions with explicit confidence and basis.

## Review And State Invariants

Status transitions must remain deterministic and inspectable.

- `normalized` means parsed and acceptable, but not yet approved
- `needs_review` means blocked, uncertain, suspicious, or incomplete
- `approved` requires explicit user approval or narrowly defined low-risk auto-approval rules

Route to review when any of the following apply:

- missing required fields such as date, amount, or currency
- low extraction confidence
- uncertain category
- suspected duplicate
- parse ambiguity
- ambiguous receipt/statement matching

Prefer false positives in review over silent bad exports.

## Duplicate Handling Rules

Keep these categories distinct:

- exact duplicate import
- near-duplicate transaction
- recurring candidate

Rules:

- exact duplicate imports are recorded in audit history but do not create a new active export row
- near-duplicates are flagged for review, never auto-merged in V1
- recurring candidates stay active unless another rule blocks them
- duplicate scoring must be explainable from concrete signals

## Storage, Privacy, And Sync

- Local storage is the source of truth for entries, mappings, fingerprints, and audit events.
- Google Sheets is an export/review surface, not the canonical store.
- Preserve raw documents and extracted text locally by default.
- Redact or minimize sensitive data in logs.
- Sheets writes must be idempotent and keyed by stable internal IDs.
- Only approved entries sync to `normalized_entries`.

## Implementation Preferences

- Prefer TypeScript for the main service unless existing repo artifacts establish a different direction.
- Keep adapters isolated by source type.
- Keep parsing and normalization versioned where practical.
- Version export contracts and sheet column schemas before evolving them.
- Start CSV-first for statements. Treat OCR and PDF parsing as bounded, review-heavy paths.

## Testing And Verification Expectations

At minimum for meaningful changes:

1. typecheck passes
2. unit tests for changed normalization, validation, dedupe, or categorization logic pass
3. build passes
4. representative fixture coverage exists for touched adapters or parsing rules

Add or update tests when changing:

- canonical schema contracts
- status transition logic
- duplicate scoring thresholds
- mapping rule precedence
- Google Sheets export shape

If verification is skipped, report exactly what was skipped and why.

## Documentation And Planning

Keep lightweight but durable docs:

- `docs/index.md` as navigation root
- `docs/specs/` for product and schema specs
- `docs/plans/active/` and `docs/plans/completed/` for execution plans
- `docs/tech-debt.md` for recurring issues and cleanup targets

If recurring mistakes appear in reviews, codify them in checks, fixtures, or scripts.

## Autonomy Mode

Default behavior in this personal project is autonomous execution.

- Execute tasks end-to-end without waiting for step-by-step confirmation.
- Continue through implementation, verification, and cleanup by default.
- On a user `go` instruction, execute multiple consecutive work slices in the same turn before replying.
- Default autonomous batch target per `go` turn:
  - 10 logical code slices
- Intermediate updates should be brief and only when they materially affect direction, risk, or blockers.
- Stop only for critical blockers:
  - missing or conflicting requirements that materially change behavior
  - destructive actions not explicitly requested
  - security or privacy risk
  - permissions or escalation required
  - reproducible failing checks that cannot be resolved safely
  - unexpected repo state that risks overwriting unrelated work

### Turn Boundary Reality

- The coding interface is turn-based.
- Therefore, maximize useful autonomous work within each turn, then send one concise checkpoint.
- Checkpoints should include completed slices, verification status, push status, and the next slice queued.

### Batch Trigger Keyword

Use `go` as the default autonomy trigger in this repository.

- When the user says `go`, execute a 10-slice autonomous batch.
- A slice is one logical, shippable unit.
- For each slice: implement, verify, and create a commit or equivalent checkpoint artifact when the environment supports commits.

## Definition Of Done

A change is done when all are true:

1. behavior matches the requested scope and product constraints
2. provenance, duplicate handling, and review safety remain intact
3. LLM usage stays within bounded suggestion roles
4. tests, typecheck, and build were run, or skipped with explicit reason
5. no unnecessary policy duplication or architecture drift was introduced
