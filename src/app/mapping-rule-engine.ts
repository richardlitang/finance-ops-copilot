import type { CategoryDecision, MappingRule } from "../domain/schemas.js";

type MappingRuleInput = {
  merchant?: string;
  description?: string;
  lineItems?: Array<{ description: string }>;
};

function matchesPattern(value: string | undefined, pattern: string): boolean {
  if (!value) return false;
  return value.toLowerCase().includes(pattern.toLowerCase());
}

export function suggestCategoryFromRules(
  input: MappingRuleInput,
  rules: MappingRule[]
): CategoryDecision | undefined {
  const sorted = [...rules].sort((a, b) => b.priority - a.priority);
  for (const rule of sorted) {
    let matched = false;
    if (rule.field === "merchant") {
      matched = matchesPattern(input.merchant, rule.pattern);
    } else if (rule.field === "description") {
      matched = matchesPattern(input.description, rule.pattern);
    } else {
      matched = (input.lineItems ?? []).some((item) => matchesPattern(item.description, rule.pattern));
    }

    if (matched) {
      return {
        suggestedCategory: rule.targetCategory,
        confidence: 0.9,
        source: "rule",
        rationale: `Matched rule ${rule.ruleId}`,
        finalCategory: rule.targetCategory
      };
    }
  }
  return undefined;
}
