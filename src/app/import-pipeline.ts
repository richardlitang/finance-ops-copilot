import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { IntakeService } from "./intake-service.js";
import { classifySource } from "./source-classifier.js";
import { adaptBankStatementCsv } from "../adapters/statement/bank-statement-adapter.js";
import { adaptCreditCardCsv } from "../adapters/statement/credit-card-adapter.js";
import { adaptReceiptText } from "../adapters/receipt/receipt-text-adapter.js";
import { adaptReceiptImage } from "../adapters/receipt/receipt-image-adapter.js";
import type { OcrPort } from "../adapters/receipt/ocr-port.js";
import { suggestCategory } from "./category-suggester.js";
import { buildImportFingerprint } from "../domain/fingerprints.js";
import { normalizeEntry } from "./normalize-entry.js";
import { evaluateDuplicate } from "./duplicate-engine.js";
import { routeReview } from "./review-router.js";
import { EntryRepo } from "../infra/db/entry-repo.js";
import { FingerprintRepo } from "../infra/db/fingerprint-repo.js";
import { MappingRuleRepo } from "../infra/db/mapping-rule-repo.js";
import { AuditService } from "./audit-service.js";
import type { LlmCategoryPort } from "../adapters/llm/llm-port.js";
import type { NormalizedEntry } from "../domain/schemas.js";

type ImportPipelineDeps = {
  intakeService: IntakeService;
  entryRepo: EntryRepo;
  fingerprintRepo: FingerprintRepo;
  mappingRuleRepo: MappingRuleRepo;
  auditService: AuditService;
  ocrPort?: OcrPort;
  llmPort?: LlmCategoryPort;
};

export class ImportPipeline {
  constructor(private readonly deps: ImportPipelineDeps) {}

  async run(filePath: string, sourceHint?: string): Promise<NormalizedEntry[]> {
    const filename = path.basename(filePath);
    const mimeType = this.inferMime(filename);
    const textLike = mimeType === "text/csv" || mimeType === "text/plain";
    const content = textLike ? fs.readFileSync(filePath, "utf8") : "";
    const classifier = classifySource({
      filename,
      sourceHint,
      rawText: content.slice(0, 2000)
    });

    const intake = this.deps.intakeService.createIntake({
      filename,
      mimeType,
      sourceType: classifier.sourceType,
      sourceHint,
      rawText: content || undefined
    });

    const candidates = await this.extractCandidates(classifier.sourceType, filePath, content);
    const rules = this.deps.mappingRuleRepo.list();
    const existingEntries = this.deps.entryRepo.listAll();
    const knownFingerprints = this.deps.fingerprintRepo.asMap();
    const created: NormalizedEntry[] = [];

    for (const candidate of candidates) {
      const entryId = randomUUID();
      const fingerprint = buildImportFingerprint({
        rawDate: candidate.transactionDateRaw,
        rawDescription: candidate.descriptionRaw ?? candidate.merchantRaw,
        rawAmount: candidate.amountRaw,
        rawReference: candidate.referenceRaw
      });
      const duplicateCheck = evaluateDuplicate({
        candidate: {
          entryId,
          amount: Number((candidate.amountRaw ?? "").replace(/[,\s]/g, "")),
          merchantNormalized: candidate.merchantRaw?.toLowerCase(),
          transactionDate: candidate.transactionDateRaw,
          description: candidate.descriptionRaw,
          importFingerprint: fingerprint
        },
        existing: existingEntries,
        knownFingerprints
      });
      const categoryDecision = await suggestCategory(
        {
          merchant: candidate.merchantRaw,
          description: candidate.descriptionRaw,
          lineItems: candidate.lineItems,
          amount: Number((candidate.amountRaw ?? "").replace(/[,\s]/g, "")),
          currency: candidate.currencyRaw
        },
        rules,
        this.deps.llmPort
      );

      const initial = normalizeEntry({
        entryId,
        sourceDocument: intake.document,
        candidate,
        extractionMeta: {
          extractorVersion: "v1",
          rawText: candidate.rawText,
          rawRowJson: candidate.rawRow ? JSON.stringify(candidate.rawRow) : undefined,
          confidence: candidate.confidence ?? 0.6,
          warnings: candidate.warnings ?? []
        },
        categoryDecision,
        duplicateCheck,
        status: "normalized",
        reviewReasons: []
      });

      const route = routeReview(initial);
      const finalEntry: NormalizedEntry = {
        ...initial,
        status: route.status,
        reviewReasons: route.reviewReasons
      };
      this.deps.entryRepo.upsert(finalEntry);
      this.deps.fingerprintRepo.upsert(fingerprint, entryId, new Date().toISOString());
      this.deps.auditService.record({
        entryId,
        eventType: "entry_normalized",
        payload: {
          sourceType: classifier.sourceType,
          duplicateStatus: duplicateCheck.status,
          status: finalEntry.status
        }
      });
      created.push(finalEntry);
    }

    return created;
  }

  private inferMime(filename: string): string {
    const lower = filename.toLowerCase();
    if (lower.endsWith(".csv")) return "text/csv";
    if (lower.endsWith(".txt")) return "text/plain";
    if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
    if (lower.endsWith(".png")) return "image/png";
    return "application/octet-stream";
  }

  private async extractCandidates(
    sourceType: "receipt" | "bank_statement" | "credit_card_statement",
    filePath: string,
    content: string
  ): Promise<
    Array<{
      merchantRaw?: string;
      descriptionRaw?: string;
      referenceRaw?: string;
      transactionDateRaw?: string;
      postingDateRaw?: string;
      amountRaw?: string;
      currencyRaw?: string;
      taxAmountRaw?: string;
      lineItems?: Array<{ description: string; amount?: number }>;
      confidence?: number;
      warnings?: string[];
      rawText?: string;
      rawRow?: Record<string, string>;
    }>
  > {
    if (sourceType === "bank_statement") {
      return adaptBankStatementCsv(content);
    }
    if (sourceType === "credit_card_statement") {
      return adaptCreditCardCsv(content);
    }

    const ext = path.extname(filePath).toLowerCase();
    if ((ext === ".jpg" || ext === ".jpeg" || ext === ".png") && this.deps.ocrPort) {
      const candidate = await adaptReceiptImage({ filePath }, this.deps.ocrPort);
      return [candidate];
    }
    return [adaptReceiptText({ text: content, filename: filePath })];
  }
}
