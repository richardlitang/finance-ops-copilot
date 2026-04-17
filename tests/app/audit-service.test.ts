import fs from "node:fs";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { createDb } from "../../src/infra/db/client.js";
import { AuditRepo } from "../../src/infra/db/audit-repo.js";
import { AuditService } from "../../src/app/audit-service.js";

const tmpDir = path.resolve(".tmp");
let dbPathCounter = 0;

function setup() {
  fs.mkdirSync(tmpDir, { recursive: true });
  const dbPath = path.join(tmpDir, `audit-${dbPathCounter++}.sqlite`);
  const db = createDb(dbPath);
  db.exec(fs.readFileSync(path.resolve("src/infra/db/migrations/001_foundation.sql"), "utf8"));
  return { db, dbPath };
}

afterEach(() => {
  for (const file of fs.readdirSync(tmpDir)) {
    if (file.startsWith("audit-") && file.endsWith(".sqlite")) {
      fs.rmSync(path.join(tmpDir, file), { force: true });
    }
  }
});

describe("AuditService", () => {
  it("writes structured audit events", () => {
    const { db } = setup();
    const service = new AuditService(new AuditRepo(db));

    const event = service.record({
      entryId: "entry_1",
      eventType: "entry_normalized",
      payload: { status: "needs_review" }
    });

    expect(event.entryId).toBe("entry_1");
    expect(event.eventType).toBe("entry_normalized");
    db.close();
  });
});
