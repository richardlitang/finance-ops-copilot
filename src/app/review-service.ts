import { AuditService } from "./audit-service.js";
import { EntryRepo } from "../infra/db/entry-repo.js";
import type { Category, DuplicateStatus } from "../domain/enums.js";
import type { NormalizedEntry } from "../domain/schemas.js";

export class ReviewService {
  constructor(
    private readonly entryRepo: EntryRepo,
    private readonly auditService: AuditService
  ) {}

  listQueue(): NormalizedEntry[] {
    return this.entryRepo.listByStatus("needs_review");
  }

  approveEntry(entryId: string): NormalizedEntry {
    const entry = this.requireEntry(entryId);
    this.entryRepo.updateStatus(entryId, "approved", [], new Date().toISOString());
    this.auditService.record({ entryId, eventType: "entry_approved", actor: "user", payload: { action: "approve" } });
    return this.requireEntry(entryId);
  }

  editCategory(entryId: string, finalCategory: Category): NormalizedEntry {
    const entry = this.requireEntry(entryId);
    const next = {
      ...entry.categoryDecision,
      finalCategory,
      source: entry.categoryDecision.source === "rule" ? "mixed" : entry.categoryDecision.source
    };
    this.entryRepo.updateCategoryDecision(entryId, JSON.stringify(next), new Date().toISOString());
    this.auditService.record({
      entryId,
      eventType: "category_suggested",
      actor: "user",
      payload: { action: "edit_category", finalCategory }
    });
    return this.requireEntry(entryId);
  }

  markDuplicate(entryId: string, relatedEntryId?: string): NormalizedEntry {
    return this.setDuplicateStatus(entryId, "exact_duplicate_import", relatedEntryId);
  }

  ignoreDuplicateWarning(entryId: string): NormalizedEntry {
    return this.setDuplicateStatus(entryId, "none");
  }

  rejectMalformed(entryId: string): NormalizedEntry {
    this.entryRepo.updateStatus(entryId, "needs_review", ["parse_error"], new Date().toISOString());
    this.auditService.record({ entryId, eventType: "entry_rejected", actor: "user", payload: { action: "reject_malformed" } });
    return this.requireEntry(entryId);
  }

  private setDuplicateStatus(entryId: string, status: DuplicateStatus, relatedEntryId?: string): NormalizedEntry {
    const entry = this.requireEntry(entryId);
    const next = {
      ...entry.duplicateCheck,
      status,
      relatedEntryId,
      confidence: status === "none" ? 0.05 : 1
    };
    this.entryRepo.updateDuplicateCheck(entryId, JSON.stringify(next), new Date().toISOString());
    this.auditService.record({
      entryId,
      eventType: "duplicate_checked",
      actor: "user",
      payload: { action: "set_duplicate_status", status, relatedEntryId }
    });
    return this.requireEntry(entryId);
  }

  private requireEntry(entryId: string): NormalizedEntry {
    const found = this.entryRepo.findById(entryId);
    if (!found) {
      throw new Error(`entry not found: ${entryId}`);
    }
    return found;
  }
}
