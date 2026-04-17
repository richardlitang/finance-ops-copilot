import { describe, expect, it } from "vitest";
import { adaptReceiptImage } from "../../../src/adapters/receipt/receipt-image-adapter.js";
import type { OcrPort } from "../../../src/adapters/receipt/ocr-port.js";

class FakeOcrPort implements OcrPort {
  async extractTextFromImage(): Promise<string> {
    return "SM SUPERMARKET\nDate: 04/16/2026\nTotal: 420.50 PHP";
  }
}

class FailingOcrPort implements OcrPort {
  async extractTextFromImage(): Promise<string> {
    throw new Error("ocr unavailable");
  }
}

describe("adaptReceiptImage", () => {
  it("uses OCR output and parses receipt text", async () => {
    const result = await adaptReceiptImage({ filePath: "receipt.jpg" }, new FakeOcrPort());
    expect(result.amountRaw).toBe("420.50");
    expect(result.confidence).toBeGreaterThan(0.6);
  });

  it("returns low-confidence candidate when OCR fails", async () => {
    const result = await adaptReceiptImage({ filePath: "receipt.jpg" }, new FailingOcrPort());
    expect(result.confidence).toBeLessThan(0.2);
    expect(result.warnings).toContain("ocr_failed");
  });
});
