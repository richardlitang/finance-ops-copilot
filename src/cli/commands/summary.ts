import { createRuntime } from "../runtime.js";
import { buildMonthlySummary } from "../../app/monthly-summary-service.js";

export async function runSummaryCommand(): Promise<void> {
  const runtime = createRuntime();
  try {
    const entries = runtime.repos.entryRepo.listAll();
    const summaryRows = buildMonthlySummary(entries);
    await runtime.services.sheetsService.syncMonthlySummary(summaryRows);
    console.log(`summary_rows=${summaryRows.length}`);
  } finally {
    runtime.db.close();
  }
}
