import path from "node:path";
import type { MappingRule } from "../domain/schemas.js";

export type SmokeFixture = {
  label: string;
  filePath: string;
  sourceHint: string;
};

export function getSmokeFixtures(): SmokeFixture[] {
  return [
    {
      label: "ph-receipt",
      filePath: path.resolve("src/fixtures/receipts/receipt-text.txt"),
      sourceHint: "receipt_text"
    },
    {
      label: "us-receipt",
      filePath: path.resolve("src/fixtures/receipts/us-receipt-text.txt"),
      sourceHint: "receipt_text"
    },
    {
      label: "bank-statement",
      filePath: path.resolve("src/fixtures/statements/bank-sample.csv"),
      sourceHint: "bank_statement"
    },
    {
      label: "credit-card-statement",
      filePath: path.resolve("src/fixtures/statements/credit-card-sample.csv"),
      sourceHint: "credit_card_statement"
    },
    {
      label: "bank-statement-duplicate",
      filePath: path.resolve("src/fixtures/statements/bank-sample.csv"),
      sourceHint: "bank_statement"
    }
  ];
}

export function getSmokeMappingRules(nowIso = new Date().toISOString()): MappingRule[] {
  return [
    {
      ruleId: "smoke_rule_sm_supermarket",
      field: "merchant",
      pattern: "SM SUPERMARKET",
      targetCategory: "groceries",
      priority: 100,
      createdBy: "system",
      createdAt: nowIso
    },
    {
      ruleId: "smoke_rule_sm_supermarket_desc",
      field: "description",
      pattern: "SM SUPERMARKET",
      targetCategory: "groceries",
      priority: 99,
      createdBy: "system",
      createdAt: nowIso
    },
    {
      ruleId: "smoke_rule_whole_foods",
      field: "merchant",
      pattern: "WHOLE FOODS",
      targetCategory: "groceries",
      priority: 100,
      createdBy: "system",
      createdAt: nowIso
    },
    {
      ruleId: "smoke_rule_spotify",
      field: "merchant",
      pattern: "SPOTIFY",
      targetCategory: "subscriptions",
      priority: 100,
      createdBy: "system",
      createdAt: nowIso
    },
    {
      ruleId: "smoke_rule_airline",
      field: "merchant",
      pattern: "AIRLINE",
      targetCategory: "travel",
      priority: 100,
      createdBy: "system",
      createdAt: nowIso
    },
    {
      ruleId: "smoke_rule_freelance_client",
      field: "description",
      pattern: "FREELANCE CLIENT",
      targetCategory: "income",
      priority: 100,
      createdBy: "system",
      createdAt: nowIso
    }
  ];
}
