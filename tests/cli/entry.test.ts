import { afterEach, describe, expect, it, vi } from "vitest";
import { runEntryCommand } from "../../src/cli/commands/entry.js";
import { createRuntime } from "../../src/cli/runtime.js";
import { runMigrations } from "../../src/infra/db/migrate.js";
import { cleanupTempDatabases } from "../helpers/test-db.js";

afterEach(() => {
  cleanupTempDatabases("entry");
  vi.restoreAllMocks();
});

describe("runEntryCommand", () => {
  it("shows a normalized entry for an imported fixture", async () => {
    runMigrations({ dbPath: ".tmp/entry-test.sqlite" });
    const runtime = createRuntime({
      dbPath: ".tmp/entry-test.sqlite",
      env: {
        GOOGLE_SHEETS_ENABLED: "false"
      }
    });

    try {
      const entries = await runtime.services.importPipeline.run("src/fixtures/receipts/receipt-text.txt", "receipt_text");
      const entryId = entries[0]?.entryId;
      expect(entryId).toBeTruthy();

      const lines: string[] = [];
      const spy = vi.spyOn(console, "log").mockImplementation((value?: unknown) => {
        lines.push(String(value ?? ""));
      });

      await runEntryCommand(["show", String(entryId)], {
        dbPath: ".tmp/entry-test.sqlite",
        env: { GOOGLE_SHEETS_ENABLED: "false" }
      });

      spy.mockRestore();
      expect(lines[0]).toContain(`entry=${entryId}`);
      expect(lines[0]).toContain("status=");
      expect(lines[1]).toContain("source_type=receipt");
      expect(lines[1]).toContain("amount=");
      expect(lines[1]).toContain("currency=");
      expect(lines[1]).toContain("category=");
    } finally {
      runtime.db.close();
    }
  });
});
