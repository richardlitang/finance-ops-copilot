import type Database from "better-sqlite3";
import { mappingRuleSchema, type MappingRule } from "../../domain/schemas.js";

export class MappingRuleRepo {
  constructor(private readonly db: Database.Database) {}

  upsert(rule: MappingRule): MappingRule {
    const valid = mappingRuleSchema.parse(rule);
    this.db
      .prepare(
        `INSERT INTO mapping_rules (
          rule_id, field, pattern, target_category, priority, created_by, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(rule_id) DO UPDATE SET
          field=excluded.field,
          pattern=excluded.pattern,
          target_category=excluded.target_category,
          priority=excluded.priority,
          created_by=excluded.created_by,
          created_at=excluded.created_at`
      )
      .run(
        valid.ruleId,
        valid.field,
        valid.pattern,
        valid.targetCategory,
        valid.priority,
        valid.createdBy,
        valid.createdAt
      );
    return valid;
  }

  list(): MappingRule[] {
    const rows = this.db.prepare("SELECT * FROM mapping_rules ORDER BY priority DESC, rule_id ASC").all() as Array<
      Record<string, unknown>
    >;
    return rows.map((row) =>
      mappingRuleSchema.parse({
        ruleId: row.rule_id,
        field: row.field,
        pattern: row.pattern,
        targetCategory: row.target_category,
        priority: row.priority,
        createdBy: row.created_by,
        createdAt: row.created_at
      })
    );
  }
}
