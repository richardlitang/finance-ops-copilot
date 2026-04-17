import { describe, expect, it } from "vitest";
import { classifySource } from "../../src/app/source-classifier.js";

describe("classifySource", () => {
  it("uses explicit hints first", () => {
    const result = classifySource({ sourceHint: "receipt_upload" });
    expect(result.sourceType).toBe("receipt");
    expect(result.confidence).toBeGreaterThan(0.9);
  });

  it("classifies card statements from filename cues", () => {
    const result = classifySource({ filename: "visa-credit-card-apr.csv", mimeType: "text/csv" });
    expect(result.sourceType).toBe("credit_card_statement");
  });

  it("falls back when ambiguous", () => {
    const result = classifySource({ filename: "unknown.dat", mimeType: "application/octet-stream" });
    expect(result.usedFallback).toBe(true);
  });
});
