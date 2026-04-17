import { execFile, spawnSync } from "node:child_process";
import { promisify } from "node:util";
import type { OcrPort } from "./ocr-port.js";

const execFileAsync = promisify(execFile);
type ExecFileResult = { stdout: string; stderr: string };
type ExecFileFn = (file: string, args: string[]) => Promise<ExecFileResult>;

type TesseractRecognizeResult = {
  data?: {
    text?: string;
  };
};

type RecognizeFn = (filePath: string, language: string) => Promise<TesseractRecognizeResult>;

const defaultRecognize: RecognizeFn = async (filePath, language) => {
  const mod = await import("tesseract.js");
  const recognize = mod.default?.recognize ?? (mod as { recognize?: RecognizeFn }).recognize;
  if (!recognize) {
    throw new Error("tesseract.js recognize function is unavailable");
  }
  return recognize(filePath, language);
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

export class TesseractCliOcrPort implements OcrPort {
  constructor(
    private readonly language = "eng",
    private readonly binaryPath = "tesseract",
    private readonly execFn: ExecFileFn = (file, args) => execFileAsync(file, args)
  ) {}

  async extractTextFromImage(filePath: string): Promise<string> {
    const { stdout } = await this.execFn(this.binaryPath, [filePath, "stdout", "-l", this.language]);
    const text = stdout.trim();
    if (!text) {
      throw new Error(`no OCR text extracted for ${filePath}`);
    }
    return text;
  }
}

export function hasLocalTesseractBinary(binaryPath = "tesseract"): boolean {
  const result = spawnSync(binaryPath, ["--version"], { stdio: "ignore" });
  return result.status === 0;
}

export function shouldUseTesseractOcr(env: NodeJS.ProcessEnv): boolean {
  return env.OCR_PROVIDER === "tesseract";
}
