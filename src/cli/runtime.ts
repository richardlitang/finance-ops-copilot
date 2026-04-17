import type Database from "better-sqlite3";
import { createDb } from "../infra/db/client.js";
import { DocumentRepo } from "../infra/db/document-repo.js";
import { EntryRepo } from "../infra/db/entry-repo.js";
import { MappingRuleRepo } from "../infra/db/mapping-rule-repo.js";
import { AuditRepo } from "../infra/db/audit-repo.js";
import { FingerprintRepo } from "../infra/db/fingerprint-repo.js";
import { IntakeService } from "../app/intake-service.js";
import { AuditService } from "../app/audit-service.js";
import { ImportPipeline } from "../app/import-pipeline.js";
import { ReviewService } from "../app/review-service.js";
import { GoogleSheetsService, type SheetsGateway } from "../adapters/sheets/google-sheets-service.js";
import { GoogleSheetsGateway, shouldUseGoogleSheetsGateway } from "../adapters/sheets/google-sheets-gateway.js";
import { TesseractOcrPort, shouldUseTesseractOcr } from "../adapters/receipt/tesseract-ocr.js";
import type { OcrPort } from "../adapters/receipt/ocr-port.js";

export class ConsoleSheetsGateway implements SheetsGateway {
  async upsertRows(tab: string, rows: Array<Record<string, unknown>>, keyField: string): Promise<void> {
    console.log(`sync tab=${tab} key=${keyField} rows=${rows.length}`);
  }
}

export type CreateRuntimeOptions = {
  env?: NodeJS.ProcessEnv;
  sheetsGateway?: SheetsGateway;
  ocrPort?: OcrPort;
};

export type CliRuntime = {
  db: Database.Database;
  repos: {
    documentRepo: DocumentRepo;
    entryRepo: EntryRepo;
    mappingRuleRepo: MappingRuleRepo;
    auditRepo: AuditRepo;
    fingerprintRepo: FingerprintRepo;
  };
  services: {
    intakeService: IntakeService;
    auditService: AuditService;
    importPipeline: ImportPipeline;
    reviewService: ReviewService;
    sheetsService: GoogleSheetsService;
  };
};

export function createOcrPortFromEnv(env: NodeJS.ProcessEnv): OcrPort | undefined {
  return shouldUseTesseractOcr(env) ? new TesseractOcrPort(env.OCR_LANGUAGE ?? "eng") : undefined;
}

export function createSheetsGatewayFromEnv(env: NodeJS.ProcessEnv): SheetsGateway {
  if (
    shouldUseGoogleSheetsGateway(env) &&
    env.GOOGLE_SHEETS_SPREADSHEET_ID &&
    env.GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON
  ) {
    return new GoogleSheetsGateway({
      spreadsheetId: env.GOOGLE_SHEETS_SPREADSHEET_ID,
      serviceAccountJson: env.GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON
    });
  }
  return new ConsoleSheetsGateway();
}

export function createRuntime(options: CreateRuntimeOptions = {}): CliRuntime {
  const env = options.env ?? process.env;
  const db = createDb();
  const documentRepo = new DocumentRepo(db);
  const entryRepo = new EntryRepo(db);
  const mappingRuleRepo = new MappingRuleRepo(db);
  const auditRepo = new AuditRepo(db);
  const fingerprintRepo = new FingerprintRepo(db);
  const intakeService = new IntakeService(documentRepo);
  const auditService = new AuditService(auditRepo);
  const ocrPort: OcrPort | undefined = options.ocrPort ?? createOcrPortFromEnv(env);

  const importPipeline = new ImportPipeline({
    intakeService,
    entryRepo,
    fingerprintRepo,
    mappingRuleRepo,
    auditService,
    ocrPort
  });
  const reviewService = new ReviewService(entryRepo, auditService);
  const gateway: SheetsGateway = options.sheetsGateway ?? createSheetsGatewayFromEnv(env);
  const sheetsService = new GoogleSheetsService(gateway);

  return {
    db,
    repos: { documentRepo, entryRepo, mappingRuleRepo, auditRepo, fingerprintRepo },
    services: { intakeService, auditService, importPipeline, reviewService, sheetsService }
  };
}
