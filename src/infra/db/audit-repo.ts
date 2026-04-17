import type Database from "better-sqlite3";
import { auditEventSchema, type AuditEvent } from "../../domain/schemas.js";

export class AuditRepo {
  constructor(private readonly db: Database.Database) {}

  insert(event: AuditEvent): AuditEvent {
    const valid = auditEventSchema.parse(event);
    this.db
      .prepare(
        `INSERT INTO audit_events (
          event_id, entry_id, event_type, event_at, actor, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?)`
      )
      .run(valid.eventId, valid.entryId, valid.eventType, valid.eventAt, valid.actor, valid.payloadJson);
    return valid;
  }

  listByEntryId(entryId: string): AuditEvent[] {
    const rows = this.db
      .prepare(
        `SELECT event_id, entry_id, event_type, event_at, actor, payload_json
         FROM audit_events WHERE entry_id = ? ORDER BY event_at ASC`
      )
      .all(entryId) as Array<Record<string, unknown>>;

    return rows.map((row) =>
      auditEventSchema.parse({
        eventId: row.event_id,
        entryId: row.entry_id,
        eventType: row.event_type,
        eventAt: row.event_at,
        actor: row.actor,
        payloadJson: row.payload_json
      })
    );
  }
}
