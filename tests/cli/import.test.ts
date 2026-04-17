import { afterEach, describe, expect, it, vi } from "vitest";
import { runImportCommand } from "../../src/cli/commands/import.js";
import { runMigrations } from "../../src/infra/db/migrate.js";
import { cleanupTempDatabases } from "../helpers/test-db.js";

afterEach(() => {
  cleanupTempDatabases("import");
  vi.restoreAllMocks();
});

describe("runImportCommand", () => {
  it("prints follow-up inspection hints when --show is enabled", async () => {
    runMigrations({ dbPath: ".tmp/import-test.sqlite" });

    const lines: string[] = [];
    const spy = vi.spyOn(console, "log").mockImplementation((value?: unknown) => {
      lines.push(String(value ?? ""));
    });

    await runImportCommand(["src/fixtures/receipts/receipt-text.txt", "receipt_text", "--show"], {
      dbPath: ".tmp/import-test.sqlite",
      env: { GOOGLE_SHEETS_ENABLED: "false" }
    });

    spy.mockRestore();
    expect(lines[0]).toContain("imported entries=1");
    expect(lines[1]).toContain("status=");
    expect(lines[2]).toContain("copilot entry show");
    expect(lines[3]).toContain("copilot candidates entry");
  });
});
