import fs from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { adaptReceiptText } from "../../../src/adapters/receipt/receipt-text-adapter.js";

describe("adaptReceiptText", () => {
  it("extracts core receipt fields from pre-extracted text", () => {
    const text = fs.readFileSync(path.resolve("src/fixtures/receipts/receipt-text.txt"), "utf8");
    const result = adaptReceiptText({ text });
    expect(result.merchantRaw).toBe("SM SUPERMARKET");
    expect(result.amountRaw).toBe("420.50");
    expect(result.currencyRaw).toBe("PHP");
    expect(result.confidence).toBeGreaterThan(0.7);
  });
});
