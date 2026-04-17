export interface OcrPort {
  extractTextFromImage(filePath: string): Promise<string>;
}
