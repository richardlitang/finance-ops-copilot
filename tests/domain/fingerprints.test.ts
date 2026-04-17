import { describe, expect, it } from "vitest";
import { buildImportFingerprint } from "../../src/domain/fingerprints.js";

describe("buildImportFingerprint", () => {
  it("is stable for semantically equivalent rows", () => {
    const a = buildImportFingerprint({
      institutionName: "My Bank",
      accountSuffix: "1234",
      rawDate: "2026-04-16",
      rawDescription: "SM SUPERMARKET",
      rawAmount: "420.50",
      rawReference: "Ref-1"
    });

    const b = buildImportFingerprint({
      institutionName: "my bank",
      accountSuffix: "1234",
      rawDate: "2026-04-16",
      rawDescription: "  SM   SUPERMARKET  ",
      rawAmount: "420.50",
      rawReference: "ref-1"
    });

    expect(a).toBe(b);
  });

  it("changes when source row data changes", () => {
    const a = buildImportFingerprint({
      rawDate: "2026-04-16",
      rawDescription: "SM SUPERMARKET",
      rawAmount: "420.50"
    });
    const b = buildImportFingerprint({
      rawDate: "2026-04-16",
      rawDescription: "GRAB",
      rawAmount: "420.50"
    });

    expect(a).not.toBe(b);
  });
});
