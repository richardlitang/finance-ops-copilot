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

  it("extracts european total formats with decimal commas", () => {
    const text = "ALDI\nDate: 17/04/2026\nA PAYER 42,97\nTotal: 42,97 EUR\nTVA 2,43";
    const result = adaptReceiptText({ text });
    expect(result.amountRaw).toBe("42,97");
    expect(result.currencyRaw).toBe("EUR");
    expect(result.taxAmountRaw).toBe("2,43");
  });

  it("extracts product line items without polluting them with receipt metadata", () => {
    const text = fs.readFileSync(path.resolve("src/fixtures/receipts/aldi-items-text.txt"), "utf8");
    const result = adaptReceiptText({ text });

    expect(result.lineItems).toEqual([
      { description: "POMME ROYAL GALA PAR K", amount: 2.43 },
      { description: "THON AU NATUREL 195G", amount: 2.58 },
      { description: "RIZ BIO FAIRTRADE", amount: 1.99 },
      { description: "B-OEUFS ELEVEES SOL 18", amount: 3.55 },
      { description: "TOMATES CERISES", amount: 0.99 },
      { description: "D-LAIT ENTIER 1L", amount: 0.89 },
      { description: "FILET SAUMON FRAIS 3X1", amount: 7.95 }
    ]);
  });
});
