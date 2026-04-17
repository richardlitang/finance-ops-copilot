import fs from "node:fs";
import { createHash } from "node:crypto";
import { parseCsv } from "../adapters/statement/csv-parser.js";
import { MappingRuleRepo } from "../infra/db/mapping-rule-repo.js";
import type { MappingRule } from "../domain/schemas.js";

type ImportMappingRulesOptions = {
  defaultCreatedBy?: MappingRule["createdBy"];
  nowIso?: string;
};

const RULE_HEADER_ALIASES: Record<string, string> = {
  id: "rule_id",
  ruleid: "rule_id",
  applies_to: "field",
  applies_to_field: "field",
  match_field: "field",
  category: "target_category",
  target: "target_category",
  createdby: "created_by"
};

function stableRuleId(field: string, pattern: string, targetCategory: string): string {
  const hash = createHash("sha1")
    .update(`${field}|${pattern.trim().toLowerCase()}|${targetCategory}`)
    .digest("hex")
    .slice(0, 10);
  return `rule_${hash}`;
}

function parsePriority(value: string | undefined): number {
  if (!value || value.trim() === "") {
    return 50;
  }
  const parsed = Number.parseInt(value, 10);
  return Number.isNaN(parsed) ? 50 : parsed;
}

function normalizeField(value: string | undefined): MappingRule["field"] {
  const normalized = (value ?? "").trim().toLowerCase();
  if (normalized === "merchant" || normalized === "description" || normalized === "line_item") {
    return normalized;
  }
  throw new Error(`invalid rule field: ${value ?? ""}`);
}

function buildRule(row: Record<string, string>, options: ImportMappingRulesOptions): MappingRule {
  const field = normalizeField(row.field);
  const pattern = row.pattern?.trim();
  const targetCategory = row.target_category?.trim();
  if (!pattern) {
    throw new Error("rule pattern is required");
  }
  if (!targetCategory) {
    throw new Error("rule target_category is required");
  }

  return {
    ruleId: row.rule_id?.trim() || stableRuleId(field, pattern, targetCategory),
    field,
    pattern,
    targetCategory: targetCategory as MappingRule["targetCategory"],
    priority: parsePriority(row.priority),
    createdBy: (row.created_by?.trim() as MappingRule["createdBy"] | undefined) ?? options.defaultCreatedBy ?? "user",
    createdAt: options.nowIso ?? new Date().toISOString()
  };
}

export function loadMappingRulesFromCsv(
  filePath: string,
  options: ImportMappingRulesOptions = {}
): MappingRule[] {
  const content = fs.readFileSync(filePath, "utf8");
  const parsed = parseCsv(content, {
    headerAliases: RULE_HEADER_ALIASES
  });

  return parsed.rows
    .filter((row) => Object.values(row).some((value) => value.trim() !== ""))
    .map((row) => buildRule(row, options));
}

export function importMappingRulesFromCsv(
  filePath: string,
  repo: MappingRuleRepo,
  options: ImportMappingRulesOptions = {}
): MappingRule[] {
  const rules = loadMappingRulesFromCsv(filePath, options);
  for (const rule of rules) {
    repo.upsert(rule);
  }
  return rules;
}
