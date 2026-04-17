import { describe, expect, it } from "vitest";
import { routeReview } from "../../src/app/review-router.js";

describe("routeReview", () => {
  it("adds parse error when extraction warnings indicate parse problems", () => {
    const result = routeReview({
      amount: 100,
      currency: "USD",
      transactionDate: "2026-04-16",
      extractionMeta: {
        extractorVersion: "v1",
        confidence: 0.9,
        warnings: ["parse failure: ambiguous amount"]
      },
      categoryDecision: {
        suggestedCategory: "shopping",
        confidence: 0.9,
        source: "rule"
      },
      duplicateCheck: {
        status: "none",
        confidence: 0.1,
        signals: []
      }
    });

    expect(result.status).toBe("needs_review");
    expect(result.reviewReasons).toContain("parse_error");
  });
});
