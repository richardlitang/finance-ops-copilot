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

  it("maps provider-style credit card headers into canonical candidate fields", () => {
    const csv = fs.readFileSync(path.resolve("src/fixtures/statements/credit-card-us-profile-sample.csv"), "utf8");
    const rows = adaptCreditCardCsv(csv, { accountHint: "card_2" });
    expect(rows).toHaveLength(2);
    expect(rows[0]?.transactionDateRaw).toBe("04/14/2026");
    expect(rows[0]?.postingDateRaw).toBe("04/15/2026");
    expect(rows[0]?.merchantRaw).toBe("NETFLIX");
    expect(rows[0]?.referenceRaw).toBe("USREF1");
    expect(rows[0]?.amountRaw).toBe("15.49");
  });
});
