import { describe, expect, it } from "vitest";
import { suggestCategoryFromRules } from "../../src/app/mapping-rule-engine.js";
import type { MappingRule } from "../../src/domain/schemas.js";

const now = "2026-04-17T00:00:00+00:00";
const rules: MappingRule[] = [
  {
    ruleId: "rule_1",
    field: "merchant",
    pattern: "GRAB",
    targetCategory: "transport",
    priority: 5,
    createdBy: "system",
    createdAt: now
  },
  {
    ruleId: "rule_2",
    field: "description",
    pattern: "ATM FEE",
    targetCategory: "fees",
    priority: 10,
    createdBy: "system",
    createdAt: now
  }
];

describe("suggestCategoryFromRules", () => {
  it("applies highest-priority matching rule", () => {
    const result = suggestCategoryFromRules(
      { merchant: "GRAB PH", description: "ATM FEE CHARGE" },
      rules
    );
    expect(result?.suggestedCategory).toBe("fees");
  });

  it("returns undefined when no rule matches", () => {
    const result = suggestCategoryFromRules({ merchant: "UNKNOWN" }, rules);
    expect(result).toBeUndefined();
  });
});
