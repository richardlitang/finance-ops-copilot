import type { CategoryDecision, MappingRule } from "../domain/schemas.js";
import { suggestCategoryFromRules } from "./mapping-rule-engine.js";
import type { LlmCategoryPort } from "../adapters/llm/llm-port.js";

type CategorySuggesterInput = {
  merchant?: string;
  description?: string;
  lineItems?: Array<{ description: string }>;
  amount?: number;
  currency?: string;
};

export async function suggestCategory(
  input: CategorySuggesterInput,
  rules: MappingRule[],
  llmPort?: LlmCategoryPort
): Promise<CategoryDecision> {
  const ruleResult = suggestCategoryFromRules(input, rules);
  if (ruleResult) {
    return ruleResult;
  }

  if (llmPort) {
    const llm = await llmPort.suggestCategory({
      merchant: input.merchant,
      description: input.description,
      amount: input.amount,
      currency: input.currency
    });
    return {
      suggestedCategory: llm.suggestedCategory,
      confidence: llm.confidence,
      source: "llm",
      rationale: llm.rationale
    };
  }

  return {
    suggestedCategory: "uncategorized",
    confidence: 0.2,
    source: "mixed",
    rationale: "No mapping rule hit and no LLM fallback configured"
  };
}
