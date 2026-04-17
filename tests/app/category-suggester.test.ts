import { describe, expect, it } from "vitest";
import { suggestCategory } from "../../src/app/category-suggester.js";
import type { MappingRule } from "../../src/domain/schemas.js";
import type { LlmCategoryPort } from "../../src/adapters/llm/llm-port.js";

const now = "2026-04-17T00:00:00+00:00";
const rules: MappingRule[] = [
  {
    ruleId: "rule_1",
    field: "merchant",
    pattern: "SPOTIFY",
    targetCategory: "subscriptions",
    priority: 5,
    createdBy: "system",
    createdAt: now
  }
];

class FakeLlmPort implements LlmCategoryPort {
  async suggestCategory() {
    return {
      suggestedCategory: "travel" as const,
      confidence: 0.7,
      rationale: "merchant resembles travel provider"
    };
  }
}

describe("suggestCategory", () => {
  it("prefers mapping rules", async () => {
    const result = await suggestCategory({ merchant: "SPOTIFY" }, rules, new FakeLlmPort());
    expect(result.source).toBe("rule");
    expect(result.suggestedCategory).toBe("subscriptions");
  });

  it("uses LLM fallback when no rule matches", async () => {
    const result = await suggestCategory({ merchant: "AIRLINE" }, rules, new FakeLlmPort());
    expect(result.source).toBe("llm");
    expect(result.suggestedCategory).toBe("travel");
  });
});
