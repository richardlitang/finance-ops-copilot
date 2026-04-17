import { randomUUID } from "node:crypto";
import { AuditRepo } from "../infra/db/audit-repo.js";
import type { AuditEventType } from "../domain/enums.js";
import type { AuditEvent } from "../domain/schemas.js";

type RecordAuditInput = {
  entryId: string;
  eventType: AuditEventType;
  actor?: "system" | "user";
  payload: unknown;
  atIso?: string;
};

export class AuditService {
  constructor(private readonly auditRepo: AuditRepo) {}

  record(input: RecordAuditInput): AuditEvent {
    const event = this.auditRepo.insert({
      eventId: randomUUID(),
      entryId: input.entryId,
      eventType: input.eventType,
      eventAt: input.atIso ?? new Date().toISOString(),
      actor: input.actor ?? "system",
      payloadJson: JSON.stringify(input.payload ?? {})
    });
    return event;
  }
}
