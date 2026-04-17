import fs from "node:fs";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { createDb } from "../../src/infra/db/client.js";
import { DocumentRepo } from "../../src/infra/db/document-repo.js";
import { IntakeService } from "../../src/app/intake-service.js";

const tmpDir = path.resolve(".tmp");
let dbPathCounter = 0;

function setup() {
  fs.mkdirSync(tmpDir, { recursive: true });
  const dbPath = path.join(tmpDir, `intake-${dbPathCounter++}.sqlite`);
  const db = createDb(dbPath);
  const schemaSql = fs.readFileSync(path.resolve("src/infra/db/migrations/001_foundation.sql"), "utf8");
  db.exec(schemaSql);
  return { db, dbPath };
}

afterEach(() => {
  for (const file of fs.readdirSync(tmpDir)) {
    if (file.startsWith("intake-") && file.endsWith(".sqlite")) {
      fs.rmSync(path.join(tmpDir, file), { force: true });
    }
  }
});

describe("IntakeService", () => {
  it("records imported document metadata and hints", () => {
    const { db } = setup();
    const repo = new DocumentRepo(db);
    const service = new IntakeService(repo);

    const result = service.createIntake({
      filename: "statement.csv",
      mimeType: "text/csv",
      sourceType: "bank_statement",
      sourceHint: "unionbank",
      localeHint: "en-PH",
      countryHint: "PH",
      rawText: "date,amount,merchant"
    });

    expect(result.document.documentId.length).toBeGreaterThan(0);
    expect(result.document.sourceType).toBe("bank_statement");
    expect(result.document.localeHint).toBe("en-PH");
    db.close();
  });
});
