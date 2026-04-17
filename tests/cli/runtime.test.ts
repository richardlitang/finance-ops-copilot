import { describe, expect, it } from "vitest";
import {
  ConsoleSheetsGateway,
  createOcrPortFromEnv,
  createRuntime,
  createSheetsGatewayFromEnv
} from "../../src/cli/runtime.js";
import { GoogleSheetsGateway } from "../../src/adapters/sheets/google-sheets-gateway.js";
import { TesseractOcrPort } from "../../src/adapters/receipt/tesseract-ocr.js";
import type { SheetsGateway } from "../../src/adapters/sheets/google-sheets-service.js";

class CaptureSheetsGateway implements SheetsGateway {
  writes = 0;
  async upsertRows(): Promise<void> {
    this.writes += 1;
  }
}

describe("runtime gateway selection", () => {
  it("defaults to console sheets gateway when google sheets env is not enabled", () => {
    const gateway = createSheetsGatewayFromEnv({
      GOOGLE_SHEETS_ENABLED: "false"
    });
    expect(gateway).toBeInstanceOf(ConsoleSheetsGateway);
  });

  it("uses GoogleSheetsGateway when required env vars are present", () => {
    const gateway = createSheetsGatewayFromEnv({
      GOOGLE_SHEETS_ENABLED: "true",
      GOOGLE_SHEETS_SPREADSHEET_ID: "spreadsheet_1",
      GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON: JSON.stringify({
        client_email: "svc@example.com",
        private_key: "-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----"
      })
    });
    expect(gateway).toBeInstanceOf(GoogleSheetsGateway);
  });
});

describe("runtime ocr selection", () => {
  it("creates tesseract ocr adapter when OCR_PROVIDER=tesseract", () => {
    const port = createOcrPortFromEnv({ OCR_PROVIDER: "tesseract", OCR_LANGUAGE: "eng" });
    expect(port).toBeInstanceOf(TesseractOcrPort);
  });

  it("disables ocr adapter by default", () => {
    const port = createOcrPortFromEnv({ OCR_PROVIDER: "none" });
    expect(port).toBeUndefined();
  });
});

describe("createRuntime overrides", () => {
  it("uses injected sheets gateway override", async () => {
    const capture = new CaptureSheetsGateway();
    const runtime = createRuntime({
      env: {
        GOOGLE_SHEETS_ENABLED: "false"
      },
      sheetsGateway: capture
    });

    await runtime.services.sheetsService.syncMonthlySummary([
      {
        month: "2026-04",
        metric_type: "currency_total",
        metric_key: "2026-04:USD",
        metric_value: 100
      }
    ]);

    expect(capture.writes).toBe(1);
    runtime.db.close();
  });
});
