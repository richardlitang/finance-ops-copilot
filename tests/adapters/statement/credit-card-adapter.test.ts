import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { adaptCreditCardCsv } from "../../../src/adapters/statement/credit-card-adapter.js";

describe("adaptCreditCardCsv", () => {
  it("maps card statement rows into candidates", () => {
    const csv = fs.readFileSync(path.resolve("src/fixtures/statements/credit-card-sample.csv"), "utf8");
    const rows = adaptCreditCardCsv(csv, { accountHint: "card_1" });
    expect(rows).toHaveLength(2);
    expect(rows[0]?.merchantRaw).toBe("SPOTIFY");
    expect(rows[0]?.referenceRaw).toBe("CCREF1");
  });
});
