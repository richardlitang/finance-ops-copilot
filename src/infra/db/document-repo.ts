import type Database from "better-sqlite3";
import { sourceDocumentRefSchema, type SourceDocumentRef } from "../../domain/schemas.js";

type DocumentRecordInput = SourceDocumentRef & {
  sourceHint?: string;
  rawText?: string;
  createdAt?: string;
};

export class DocumentRepo {
  constructor(private readonly db: Database.Database) {}

  insert(input: DocumentRecordInput): SourceDocumentRef {
    sourceDocumentRefSchema.parse(input);
    this.db
      .prepare(
        `INSERT INTO source_documents (
          document_id, source_type, filename, mime_type, imported_at, locale_hint, country_hint, source_hint, raw_text, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .run(
        input.documentId,
        input.sourceType,
        input.filename,
        input.mimeType,
        input.importedAt,
        input.localeHint ?? null,
        input.countryHint ?? null,
        input.sourceHint ?? null,
        input.rawText ?? null,
        input.createdAt ?? new Date().toISOString()
      );

    return sourceDocumentRefSchema.parse(input);
  }

  findById(documentId: string): SourceDocumentRef | null {
    const row = this.db
      .prepare(
        `SELECT document_id, source_type, filename, mime_type, imported_at, locale_hint, country_hint
         FROM source_documents WHERE document_id = ?`
      )
      .get(documentId) as
      | {
          document_id: string;
          source_type: string;
          filename: string;
          mime_type: string;
          imported_at: string;
          locale_hint: string | null;
          country_hint: string | null;
        }
      | undefined;

    if (!row) {
      return null;
    }

    return sourceDocumentRefSchema.parse({
      documentId: row.document_id,
      sourceType: row.source_type,
      filename: row.filename,
      mimeType: row.mime_type,
      importedAt: row.imported_at,
      localeHint: row.locale_hint ?? undefined,
      countryHint: row.country_hint ?? undefined
    });
  }
}
