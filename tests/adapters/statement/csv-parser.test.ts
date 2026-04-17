import { describe, expect, it } from "vitest";
import { parseCsv } from "../../../src/adapters/statement/csv-parser.js";

describe("parseCsv", () => {
  it("parses comma-delimited content with normalized headers", () => {
    const parsed = parseCsv("Date,Description,Amount\n2026-04-01,SM,420.50");
    expect(parsed.headers).toEqual(["date", "description", "amount"]);
    expect(parsed.rows[0]?.amount).toBe("420.50");
  });

  it("parses semicolon-delimited content", () => {
    const parsed = parseCsv("Date;Description;Amount\n2026-04-01;SM;420.50");
    expect(parsed.delimiter).toBe(";");
    expect(parsed.rows).toHaveLength(1);
  });
});
