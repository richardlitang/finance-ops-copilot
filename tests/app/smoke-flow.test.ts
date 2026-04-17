import fs from "node:fs";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { runSmokeFlow } from "../../src/app/smoke-flow.js";
import type { SheetsGateway } from "../../src/adapters/sheets/google-sheets-service.js";

class CaptureGateway implements SheetsGateway {
  writes: Array<{ tab: string; rowCount: number }> = [];

  async upsertRows(tab: "raw_imports" | "normalized_entries" | "review_queue" | "mapping_rules" | "monthly_summary", rows: Array<Record<string, unknown>>): Promise<void> {
    this.writes.push({ tab, rowCount: rows.length });
  }
}

const tmpDir = path.resolve(".tmp");

afterEach(() => {
  for (const file of fs.readdirSync(tmpDir)) {
    if (file.startsWith("smoke-flow-test")) {
      fs.rmSync(path.join(tmpDir, file), { force: true });
    }
  }
});

describe("runSmokeFlow", () => {
  it("executes the local happy path and surfaces duplicates without exporting them as active rows", async () => {
    const capture = new CaptureGateway();
    const lines: string[] = [];
    const result = await runSmokeFlow({
      dbPath: path.resolve(".tmp/smoke-flow-test.sqlite"),
      sheetsGateway: capture,
      logger: (line) => lines.push(line)
    });

    expect(result.importedFixtureCount).toBe(5);
    expect(result.exactDuplicateCount).toBe(2);
    expect(result.reviewQueueCount).toBe(2);
    expect(result.exportedApprovedCount).toBe(6);
    expect(result.monthlySummaryRowCount).toBeGreaterThan(0);

    expect(capture.writes.some((write) => write.tab === "normalized_entries" && write.rowCount === 6)).toBe(true);
    expect(capture.writes.some((write) => write.tab === "review_queue" && write.rowCount === 2)).toBe(true);
    expect(lines.some((line) => line.startsWith("review_queue=2 exact_duplicates=2"))).toBe(true);
  });
});
