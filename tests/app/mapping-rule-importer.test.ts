import fs from "node:fs";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { loadMappingRulesFromCsv, importMappingRulesFromCsv } from "../../src/app/mapping-rule-importer.js";
import { createDb } from "../../src/infra/db/client.js";
import { MappingRuleRepo } from "../../src/infra/db/mapping-rule-repo.js";

const tmpDir = path.resolve(".tmp");
let fileCounter = 0;

function writeTempCsv(content: string): string {
  fs.mkdirSync(tmpDir, { recursive: true });
  const filePath = path.join(tmpDir, `mapping-rules-${fileCounter++}.csv`);
  fs.writeFileSync(filePath, content);
  return filePath;
}

afterEach(() => {
  for (const file of fs.readdirSync(tmpDir)) {
    if (file.startsWith("mapping-rules-")) {
      fs.rmSync(path.join(tmpDir, file), { force: true });
    }
  }
});

describe("loadMappingRulesFromCsv", () => {
  it("loads rules and generates stable ids when omitted", () => {
    const csvPath = writeTempCsv(
      "field,pattern,target_category,priority\nmerchant,NETFLIX,subscriptions,80\ndescription,ATM FEE,fees,90\n"
    );

    const rules = loadMappingRulesFromCsv(csvPath, {
      defaultCreatedBy: "user",
      nowIso: "2026-04-17T00:00:00+00:00"
    });

    expect(rules).toHaveLength(2);
    expect(rules[0]?.ruleId.startsWith("rule_")).toBe(true);
    expect(rules[0]?.createdBy).toBe("user");
    expect(rules[1]?.targetCategory).toBe("fees");
  });

  it("accepts alias headers like category and id", () => {
    const csvPath = writeTempCsv(
      "id,applies_to,pattern,category\nrule_custom,merchant,GRAB,transport\n"
    );

    const rules = loadMappingRulesFromCsv(csvPath, {
      defaultCreatedBy: "system",
      nowIso: "2026-04-17T00:00:00+00:00"
    });

    expect(rules[0]?.ruleId).toBe("rule_custom");
    expect(rules[0]?.field).toBe("merchant");
    expect(rules[0]?.targetCategory).toBe("transport");
  });
});

describe("importMappingRulesFromCsv", () => {
  it("upserts rules into the repository", () => {
    const dbPath = path.join(tmpDir, `mapping-rules-db-${fileCounter++}.sqlite`);
    const db = createDb(dbPath);
    db.exec(fs.readFileSync(path.resolve("src/infra/db/migrations/001_foundation.sql"), "utf8"));
    const repo = new MappingRuleRepo(db);

    const csvPath = writeTempCsv(
      "rule_id,field,pattern,target_category,priority,created_by\nrule_1,merchant,WHOLE FOODS,groceries,100,system\n"
    );

    const imported = importMappingRulesFromCsv(csvPath, repo, {
      defaultCreatedBy: "system",
      nowIso: "2026-04-17T00:00:00+00:00"
    });

    expect(imported).toHaveLength(1);
    expect(repo.list()).toHaveLength(1);
    expect(repo.list()[0]?.pattern).toBe("WHOLE FOODS");

    db.close();
    fs.rmSync(dbPath, { force: true });
  });
});
