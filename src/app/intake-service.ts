import { randomUUID } from "node:crypto";
import type { SourceType } from "../domain/enums.js";
import type { SourceDocumentRef } from "../domain/schemas.js";
import { DocumentRepo } from "../infra/db/document-repo.js";

export type IntakeInput = {
  filename: string;
  mimeType: string;
  sourceType: SourceType;
  sourceHint?: string;
  localeHint?: string;
  countryHint?: string;
  rawText?: string;
};

export type IntakeResult = {
  document: SourceDocumentRef;
};

export class IntakeService {
  constructor(private readonly documentRepo: DocumentRepo) {}

  createIntake(input: IntakeInput): IntakeResult {
    const now = new Date().toISOString();
    const document = this.documentRepo.insert({
      documentId: randomUUID(),
      sourceType: input.sourceType,
      filename: input.filename,
      mimeType: input.mimeType,
      importedAt: now,
      localeHint: input.localeHint,
      countryHint: input.countryHint,
      sourceHint: input.sourceHint,
      rawText: input.rawText,
      createdAt: now
    });

    return { document };
  }
}
