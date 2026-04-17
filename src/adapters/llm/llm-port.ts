import type { Category } from "../../domain/enums.js";

export type LlmCategorySuggestionInput = {
  merchant?: string;
  description?: string;
  amount?: number;
  currency?: string;
};

export type LlmCategorySuggestion = {
  suggestedCategory: Category;
  confidence: number;
  rationale?: string;
};

export interface LlmCategoryPort {
  suggestCategory(input: LlmCategorySuggestionInput): Promise<LlmCategorySuggestion>;
}
