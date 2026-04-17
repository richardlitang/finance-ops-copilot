import type { MonthlySummaryRow } from "../adapters/sheets/sheets-contract.js";
import type { NormalizedEntry } from "../domain/schemas.js";

function monthKey(date: string | undefined): string {
  if (!date) return "unknown";
  return date.slice(0, 7);
}

function add(map: Map<string, number>, key: string, amount: number): void {
  map.set(key, (map.get(key) ?? 0) + amount);
}

export function buildMonthlySummary(entries: NormalizedEntry[]): MonthlySummaryRow[] {
  const approved = entries.filter((entry) => entry.status === "approved");
  const byCategory = new Map<string, number>();
  const byMerchant = new Map<string, number>();
  const byCurrency = new Map<string, number>();
  const uncategorizedByMonth = new Map<string, number>();
  const recurringByMonth = new Map<string, number>();

  for (const entry of approved) {
    const month = monthKey(entry.transactionDate);
    add(byCategory, `${month}:${entry.categoryDecision.finalCategory ?? entry.categoryDecision.suggestedCategory}`, entry.amount);
    add(byMerchant, `${month}:${entry.merchantNormalized ?? entry.merchantRaw ?? "unknown_merchant"}`, entry.amount);
    add(byCurrency, `${month}:${entry.currency}`, entry.amount);

    if ((entry.categoryDecision.finalCategory ?? entry.categoryDecision.suggestedCategory) === "uncategorized") {
      add(uncategorizedByMonth, month, 1);
    }
    if (entry.duplicateCheck.status === "recurring_candidate") {
      add(recurringByMonth, month, 1);
    }
  }

  const rows: MonthlySummaryRow[] = [];
  for (const [key, value] of byCategory.entries()) {
    rows.push({ month: key.split(":")[0] ?? "unknown", metric_type: "category_total", metric_key: key, metric_value: value });
  }
  for (const [key, value] of byMerchant.entries()) {
    rows.push({ month: key.split(":")[0] ?? "unknown", metric_type: "merchant_total", metric_key: key, metric_value: value });
  }
  for (const [key, value] of byCurrency.entries()) {
    rows.push({ month: key.split(":")[0] ?? "unknown", metric_type: "currency_total", metric_key: key, metric_value: value });
  }
  for (const [month, value] of recurringByMonth.entries()) {
    rows.push({ month, metric_type: "recurring_candidate", metric_key: `${month}:recurring_candidates`, metric_value: value });
  }
  for (const [month, value] of uncategorizedByMonth.entries()) {
    rows.push({ month, metric_type: "uncategorized_count", metric_key: `${month}:uncategorized_count`, metric_value: value });
  }

  return rows;
}
