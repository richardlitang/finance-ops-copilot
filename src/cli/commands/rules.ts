import path from "node:path";
import { createRuntime } from "../runtime.js";
import { importMappingRulesFromCsv } from "../../app/mapping-rule-importer.js";

const DEFAULT_RULES_FIXTURE = path.resolve("src/fixtures/mapping-rules/default-mapping-rules.csv");

export async function runRulesCommand(args: string[]): Promise<void> {
  const sub = args[0] ?? "list";
  const runtime = createRuntime();
  try {
    if (sub === "list") {
      const rules = runtime.repos.mappingRuleRepo.list();
      console.log(`mapping_rules=${rules.length}`);
      for (const rule of rules) {
        console.log(`${rule.ruleId} field=${rule.field} category=${rule.targetCategory} pattern=${rule.pattern}`);
      }
      return;
    }

    if (sub === "import" || sub === "bootstrap") {
      const filePath = args[1] ? path.resolve(args[1]) : DEFAULT_RULES_FIXTURE;
      const createdBy = (args[2] as "system" | "user" | undefined) ?? (sub === "bootstrap" ? "system" : "user");
      const imported = importMappingRulesFromCsv(filePath, runtime.repos.mappingRuleRepo, {
        defaultCreatedBy: createdBy
      });
      console.log(`mapping_rules_imported=${imported.length} source=${filePath}`);
      return;
    }

    throw new Error("usage: rules <list|import|bootstrap> [file-path] [system|user]");
  } finally {
    runtime.db.close();
  }
}
