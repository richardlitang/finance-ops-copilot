import { afterEach, describe, expect, it, vi } from "vitest";
import { runCandidatesCommand } from "../../src/cli/commands/candidates.js";
import { createRuntime } from "../../src/cli/runtime.js";
import { runMigrations } from "../../src/infra/db/migrate.js";
import { cleanupTempDatabases } from "../helpers/test-db.js";

afterEach(() => {
  cleanupTempDatabases("candidates");
  vi.restoreAllMocks();
});

describe("runCandidatesCommand", () => {
  it("lists extracted candidates for an imported entry", async () => {
    runMigrations({ dbPath: ".tmp/candidates-test.sqlite" });
    const runtime = createRuntime({
      dbPath: ".tmp/candidates-test.sqlite",
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

      await runCandidatesCommand(["entry", String(entryId)], {
        dbPath: ".tmp/candidates-test.sqlite",
        env: { GOOGLE_SHEETS_ENABLED: "false" }
      });

      spy.mockRestore();
      expect(lines[0]).toContain("candidates=1");
      expect(lines[0]).toContain(`id=${entryId}`);
      expect(lines[1]).toContain("merchant=");
      expect(lines[1]).toContain(`entry=${entryId}`);
    } finally {
      runtime.db.close();
    }
  });
});
