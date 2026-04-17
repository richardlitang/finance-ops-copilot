import { toNormalizedEntryRow, toReviewQueueRow, type MonthlySummaryRow, type SheetsTab } from "./sheets-contract.js";
import type { NormalizedEntry } from "../../domain/schemas.js";

export interface SheetsGateway {
  upsertRows(tab: SheetsTab, rows: Array<Record<string, unknown>>, keyField: string): Promise<void>;
}

export class GoogleSheetsService {
  constructor(private readonly gateway: SheetsGateway) {}

  async syncApprovedEntries(entries: NormalizedEntry[], exportedAt = new Date().toISOString()): Promise<number> {
    const approvedRows = entries
      .filter((entry) => entry.status === "approved" && entry.duplicateCheck.status !== "exact_duplicate_import")
      .map((entry) => toNormalizedEntryRow(entry, exportedAt));
    if (approvedRows.length === 0) {
      return 0;
    }
    await this.gateway.upsertRows("normalized_entries", approvedRows, "entry_id");
    return approvedRows.length;
  }

  async syncReviewQueue(entries: NormalizedEntry[]): Promise<number> {
    const reviewRows = entries.filter((entry) => entry.status === "needs_review").map(toReviewQueueRow);
    if (reviewRows.length === 0) {
      return 0;
    }
    await this.gateway.upsertRows("review_queue", reviewRows, "entry_id");
    return reviewRows.length;
  }

  async syncMonthlySummary(rows: MonthlySummaryRow[]): Promise<number> {
    if (rows.length === 0) {
      return 0;
    }
    await this.gateway.upsertRows("monthly_summary", rows as Array<Record<string, unknown>>, "metric_key");
    return rows.length;
  }
}
