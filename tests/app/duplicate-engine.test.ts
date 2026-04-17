import { describe, expect, it } from "vitest";
import { evaluateDuplicate } from "../../src/app/duplicate-engine.js";

describe("evaluateDuplicate", () => {
  it("marks exact duplicates by fingerprint", () => {
    const result = evaluateDuplicate({
      candidate: {
        entryId: "new",
        amount: 100,
        merchantNormalized: "grab",
        transactionDate: "2026-04-17",
        importFingerprint: "abc123"
      },
      existing: [],
      knownFingerprints: new Map([["abc123", "entry_1"]])
    });

    expect(result.status).toBe("exact_duplicate_import");
    expect(result.relatedEntryId).toBe("entry_1");
  });

  it("flags near duplicates by score", () => {
    const result = evaluateDuplicate({
      candidate: {
        entryId: "new",
        amount: 420.5,
        merchantNormalized: "sm supermarket",
        transactionDate: "2026-04-17",
        description: "card purchase"
      },
      existing: [
        {
          entryId: "entry_1",
          amount: 420.5,
          merchantNormalized: "sm supermarket",
          transactionDate: "2026-04-16",
          description: "card purchase"
        }
      ],
      knownFingerprints: new Map()
    });

    expect(result.status).toBe("near_duplicate_suspected");
  });

  it("marks recurring candidates separately", () => {
    const result = evaluateDuplicate({
      candidate: {
        entryId: "new",
        amount: 9.99,
        merchantNormalized: "spotify",
        transactionDate: "2026-04-30"
      },
      existing: [
        {
          entryId: "entry_1",
          amount: 9.99,
          merchantNormalized: "spotify",
          transactionDate: "2026-03-31"
        }
      ],
      knownFingerprints: new Map()
    });

    expect(result.status).toBe("recurring_candidate");
  });
});
