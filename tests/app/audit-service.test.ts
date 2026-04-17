import { afterEach, describe, expect, it } from "vitest";
import { AuditRepo } from "../../src/infra/db/audit-repo.js";
import { AuditService } from "../../src/app/audit-service.js";
import { cleanupTempDatabases, createMigratedTestDatabase } from "../helpers/test-db.js";

afterEach(() => {
  cleanupTempDatabases("audit");
});

describe("AuditService", () => {
  it("writes structured audit events", () => {
    const { db } = createMigratedTestDatabase("audit");
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
