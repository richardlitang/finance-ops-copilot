import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { adaptBankStatementCsv } from "../../../src/adapters/statement/bank-statement-adapter.js";

describe("adaptBankStatementCsv", () => {
  it("maps CSV rows into bank candidates", () => {
    const csv = fs.readFileSync(path.resolve("src/fixtures/statements/bank-sample.csv"), "utf8");
    const rows = adaptBankStatementCsv(csv, { accountHint: "acct_123" });
    expect(rows).toHaveLength(2);
    expect(rows[0]?.source).toBe("bank_statement");
    expect(rows[0]?.currencyRaw).toBe("PHP");
    expect(rows[1]?.amountRaw).toBe("1200");
  });
});
