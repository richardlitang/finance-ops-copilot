import type { OcrPort } from "./ocr-port.js";

type TesseractRecognizeResult = {
  data?: {
    text?: string;
  };
};

type RecognizeFn = (filePath: string, language: string) => Promise<TesseractRecognizeResult>;

const defaultRecognize: RecognizeFn = async (filePath, language) => {
  const mod = await import("tesseract.js");
  return mod.recognize(filePath, language);
};

export class TesseractOcrPort implements OcrPort {
  constructor(
    private readonly language = "eng",
    private readonly recognize: RecognizeFn = defaultRecognize
  ) {}

  async extractTextFromImage(filePath: string): Promise<string> {
    const result = await this.recognize(filePath, this.language);
    const text = result.data?.text?.trim();
    if (!text) {
      throw new Error(`no OCR text extracted for ${filePath}`);
    }
    return text;
  }
}

export function shouldUseTesseractOcr(env: NodeJS.ProcessEnv): boolean {
  return env.OCR_PROVIDER === "tesseract";
}
