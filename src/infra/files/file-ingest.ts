import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";

export type IngestedFile = {
  documentId: string;
  filename: string;
  mimeType: string;
  storagePath: string;
};

function inferMimeType(filename: string): string {
  const ext = path.extname(filename).toLowerCase();
  switch (ext) {
    case ".jpg":
    case ".jpeg":
      return "image/jpeg";
    case ".png":
      return "image/png";
    case ".webp":
      return "image/webp";
    case ".pdf":
      return "application/pdf";
    case ".csv":
      return "text/csv";
    case ".txt":
      return "text/plain";
    default:
      return "application/octet-stream";
  }
}

export function ingestFile(filePath: string, storeDir = path.resolve(".tmp/imports")): IngestedFile {
  fs.mkdirSync(storeDir, { recursive: true });
  const filename = path.basename(filePath);
  const documentId = randomUUID();
  const targetPath = path.join(storeDir, `${documentId}-${filename}`);
  fs.copyFileSync(filePath, targetPath);

  return {
    documentId,
    filename,
    mimeType: inferMimeType(filename),
    storagePath: targetPath
  };
}
