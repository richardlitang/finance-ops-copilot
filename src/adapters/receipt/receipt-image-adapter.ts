import type { OcrPort } from "./ocr-port.js";
import type { ReceiptCandidate } from "./receipt-text-port.js";
import { adaptReceiptText } from "./receipt-text-adapter.js";

type ReceiptImageInput = {
  filePath: string;
  localeHint?: string;
  currencyHint?: string;
};

export async function adaptReceiptImage(input: ReceiptImageInput, ocr: OcrPort): Promise<ReceiptCandidate> {
  try {
    const text = await ocr.extractTextFromImage(input.filePath);
    return adaptReceiptText({
      text,
      localeHint: input.localeHint,
      currencyHint: input.currencyHint,
      filename: input.filePath
    });
  } catch (error) {
    return {
      confidence: 0.1,
      warnings: ["ocr_failed", error instanceof Error ? error.message : "unknown_ocr_error"],
      rawText: "",
      lineItems: []
    };
  }
}
