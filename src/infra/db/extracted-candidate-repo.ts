import type Database from "better-sqlite3";
import { extractedCandidateSchema, type ExtractedCandidate } from "../../domain/schemas.js";

export class ExtractedCandidateRepo {
  constructor(private readonly db: Database.Database) {}

  private mapRow(row: Record<string, unknown>): ExtractedCandidate {
    return extractedCandidateSchema.parse({
      candidateId: row.candidate_id,
      documentId: row.document_id,
      sourceType: row.source_type,
      entryId: row.entry_id ?? undefined,
      merchantRaw: row.merchant_raw ?? undefined,
      descriptionRaw: row.description_raw ?? undefined,
      referenceRaw: row.reference_raw ?? undefined,
      transactionDateRaw: row.transaction_date_raw ?? undefined,
      postingDateRaw: row.posting_date_raw ?? undefined,
      amountRaw: row.amount_raw ?? undefined,
      currencyRaw: row.currency_raw ?? undefined,
      taxAmountRaw: row.tax_amount_raw ?? undefined,
      lineItems: JSON.parse(String(row.line_items_json)),
      confidence: row.confidence,
      warnings: JSON.parse(String(row.warnings_json)),
      rawText: row.raw_text ?? undefined,
      rawRowJson: row.raw_row_json ?? undefined,
      extractorVersion: row.extractor_version,
      createdAt: row.created_at
    });
  }

  insert(candidate: ExtractedCandidate): ExtractedCandidate {
    const valid = extractedCandidateSchema.parse(candidate);
    this.db
      .prepare(
        `INSERT INTO extracted_candidates (
          candidate_id, document_id, source_type, entry_id, merchant_raw, description_raw,
          reference_raw, transaction_date_raw, posting_date_raw, amount_raw, currency_raw,
          tax_amount_raw, line_items_json, confidence, warnings_json, raw_text, raw_row_json,
          extractor_version, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .run(
        valid.candidateId,
        valid.documentId,
        valid.sourceType,
        valid.entryId ?? null,
        valid.merchantRaw ?? null,
        valid.descriptionRaw ?? null,
        valid.referenceRaw ?? null,
        valid.transactionDateRaw ?? null,
        valid.postingDateRaw ?? null,
        valid.amountRaw ?? null,
        valid.currencyRaw ?? null,
        valid.taxAmountRaw ?? null,
        JSON.stringify(valid.lineItems),
        valid.confidence,
        JSON.stringify(valid.warnings),
        valid.rawText ?? null,
        valid.rawRowJson ?? null,
        valid.extractorVersion,
        valid.createdAt
      );

    return valid;
  }

  listByDocumentId(documentId: string): ExtractedCandidate[] {
    const rows = this.db
      .prepare(
        `SELECT *
         FROM extracted_candidates
         WHERE document_id = ?
         ORDER BY created_at ASC, candidate_id ASC`
      )
      .all(documentId) as Array<Record<string, unknown>>;
    return rows.map((row) => this.mapRow(row));
  }

  listByEntryId(entryId: string): ExtractedCandidate[] {
    const rows = this.db
      .prepare(
        `SELECT *
         FROM extracted_candidates
         WHERE entry_id = ?
         ORDER BY created_at ASC, candidate_id ASC`
      )
      .all(entryId) as Array<Record<string, unknown>>;
    return rows.map((row) => this.mapRow(row));
  }
}
