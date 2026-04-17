import { describe, expect, it } from "vitest";
import { parseCsv } from "../../../src/adapters/statement/csv-parser.js";
import { BANK_STATEMENT_HEADER_ALIASES } from "../../../src/adapters/statement/profiles.js";

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

  it("applies header aliases for provider-style CSV variants", () => {
    const parsed = parseCsv("Txn Date,Transaction Details,Reference No\n2026-04-01,GRAB,RX1", {
      headerAliases: BANK_STATEMENT_HEADER_ALIASES
    });
    expect(parsed.headers).toEqual(["transaction_date", "description", "reference"]);
    expect(parsed.rows[0]?.transaction_date).toBe("2026-04-01");
  });
});
