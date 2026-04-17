import { describe, expect, it } from "vitest";
import { TesseractOcrPort, shouldUseTesseractOcr } from "../../../src/adapters/receipt/tesseract-ocr.js";

describe("TesseractOcrPort", () => {
  it("returns trimmed text from recognize output", async () => {
    const port = new TesseractOcrPort("eng", async () => ({
      data: { text: "  hello world  " }
    }));

    const text = await port.extractTextFromImage("fake.jpg");
    expect(text).toBe("hello world");
  });

  it("throws when OCR result is empty", async () => {
    const port = new TesseractOcrPort("eng", async () => ({
      data: { text: "   " }
    }));
    await expect(port.extractTextFromImage("fake.jpg")).rejects.toThrow("no OCR text extracted");
  });
});

describe("shouldUseTesseractOcr", () => {
  it("enables only when OCR_PROVIDER=tesseract", () => {
    expect(shouldUseTesseractOcr({ OCR_PROVIDER: "tesseract" })).toBe(true);
    expect(shouldUseTesseractOcr({ OCR_PROVIDER: "none" })).toBe(false);
  });
});
