import type Database from "better-sqlite3";
import { normalizedEntrySchema, type NormalizedEntry } from "../../domain/schemas.js";

export class EntryRepo {
  constructor(private readonly db: Database.Database) {}

  private mapRowToEntry(row: Record<string, unknown>): NormalizedEntry {
    return normalizedEntrySchema.parse({
      entryId: row.entry_id,
      sourceDocument: {
        documentId: row.document_id,
        sourceType: row.source_type,
        filename: row.filename,
        mimeType: row.mime_type,
        importedAt: row.imported_at,
        localeHint: row.locale_hint ?? undefined,
        countryHint: row.country_hint ?? undefined
      },
      merchantRaw: row.merchant_raw ?? undefined,
      merchantNormalized: row.merchant_normalized ?? undefined,
      description: row.description ?? undefined,
      reference: row.reference ?? undefined,
      transactionDate: row.transaction_date ?? undefined,
      postingDate: row.posting_date ?? undefined,
      amount: row.amount,
      currency: row.currency,
      baseAmount: row.base_amount ?? undefined,
      baseCurrency: row.base_currency ?? undefined,
      taxAmount: row.tax_amount ?? undefined,
      lineItems: JSON.parse(String(row.line_items_json)),
      categoryDecision: JSON.parse(String(row.category_decision_json)),
      duplicateCheck: JSON.parse(String(row.duplicate_check_json)),
      status: row.status,
      reviewReasons: JSON.parse(String(row.review_reasons_json)),
      extractionMeta: JSON.parse(String(row.extraction_meta_json)),
      createdAt: row.created_at,
      updatedAt: row.updated_at
    });
  }

  upsert(entry: NormalizedEntry): NormalizedEntry {
    const valid = normalizedEntrySchema.parse(entry);

    this.db
      .prepare(
        `INSERT INTO normalized_entries (
          entry_id, document_id, merchant_raw, merchant_normalized, description, reference,
          transaction_date, posting_date, amount, currency, base_amount, base_currency, tax_amount,
          line_items_json, category_decision_json, duplicate_check_json, status, review_reasons_json,
          extraction_meta_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(entry_id) DO UPDATE SET
          merchant_raw=excluded.merchant_raw,
          merchant_normalized=excluded.merchant_normalized,
          description=excluded.description,
          reference=excluded.reference,
          transaction_date=excluded.transaction_date,
          posting_date=excluded.posting_date,
          amount=excluded.amount,
          currency=excluded.currency,
          base_amount=excluded.base_amount,
          base_currency=excluded.base_currency,
          tax_amount=excluded.tax_amount,
          line_items_json=excluded.line_items_json,
          category_decision_json=excluded.category_decision_json,
          duplicate_check_json=excluded.duplicate_check_json,
          status=excluded.status,
          review_reasons_json=excluded.review_reasons_json,
          extraction_meta_json=excluded.extraction_meta_json,
          updated_at=excluded.updated_at`
      )
      .run(
        valid.entryId,
        valid.sourceDocument.documentId,
        valid.merchantRaw ?? null,
        valid.merchantNormalized ?? null,
        valid.description ?? null,
        valid.reference ?? null,
        valid.transactionDate ?? null,
        valid.postingDate ?? null,
        valid.amount,
        valid.currency,
        valid.baseAmount ?? null,
        valid.baseCurrency ?? null,
        valid.taxAmount ?? null,
        JSON.stringify(valid.lineItems),
        JSON.stringify(valid.categoryDecision),
        JSON.stringify(valid.duplicateCheck),
        valid.status,
        JSON.stringify(valid.reviewReasons),
        JSON.stringify(valid.extractionMeta),
        valid.createdAt,
        valid.updatedAt
      );

    return valid;
  }

  findById(entryId: string): NormalizedEntry | null {
    const row = this.db
      .prepare(
        `SELECT
          e.*,
          d.source_type,
          d.filename,
          d.mime_type,
          d.imported_at,
          d.locale_hint,
          d.country_hint
         FROM normalized_entries e
         JOIN source_documents d ON d.document_id = e.document_id
         WHERE e.entry_id = ?`
      )
      .get(entryId) as Record<string, unknown> | undefined;
    if (!row) {
      return null;
    }

    return this.mapRowToEntry(row);
  }

  listByStatus(status: NormalizedEntry["status"]): NormalizedEntry[] {
    const rows = this.db
      .prepare(
        `SELECT
          e.*,
          d.source_type,
          d.filename,
          d.mime_type,
          d.imported_at,
          d.locale_hint,
          d.country_hint
         FROM normalized_entries e
         JOIN source_documents d ON d.document_id = e.document_id
         WHERE e.status = ?
         ORDER BY e.created_at ASC`
      )
      .all(status) as Array<Record<string, unknown>>;

    return rows.map((row) => this.mapRowToEntry(row));
  }

  listAll(): NormalizedEntry[] {
    const rows = this.db
      .prepare(
        `SELECT
          e.*,
          d.source_type,
          d.filename,
          d.mime_type,
          d.imported_at,
          d.locale_hint,
          d.country_hint
         FROM normalized_entries e
         JOIN source_documents d ON d.document_id = e.document_id
         ORDER BY e.created_at ASC`
      )
      .all() as Array<Record<string, unknown>>;

    return rows.map((row) => this.mapRowToEntry(row));
  }

  updateStatus(entryId: string, status: NormalizedEntry["status"], reviewReasons: string[], updatedAt: string): void {
    this.db
      .prepare(
        `UPDATE normalized_entries
         SET status = ?, review_reasons_json = ?, updated_at = ?
         WHERE entry_id = ?`
      )
      .run(status, JSON.stringify(reviewReasons), updatedAt, entryId);
  }

  updateCategoryDecision(entryId: string, categoryDecisionJson: string, updatedAt: string): void {
    this.db
      .prepare(
        `UPDATE normalized_entries
         SET category_decision_json = ?, updated_at = ?
         WHERE entry_id = ?`
      )
      .run(categoryDecisionJson, updatedAt, entryId);
  }

  updateDuplicateCheck(entryId: string, duplicateCheckJson: string, updatedAt: string): void {
    this.db
      .prepare(
        `UPDATE normalized_entries
         SET duplicate_check_json = ?, updated_at = ?
         WHERE entry_id = ?`
      )
      .run(duplicateCheckJson, updatedAt, entryId);
  }
}
