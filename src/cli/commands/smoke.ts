import { runSmokeFlow } from "../../app/smoke-flow.js";

export async function runSmokeCommand(): Promise<void> {
  const result = await runSmokeFlow({
    logger: (line) => console.log(line)
  });
  console.log(
    `smoke ok fixtures=${result.importedFixtureCount} entries=${result.importedEntryCount} review_queue=${result.reviewQueueCount} approved_exported=${result.exportedApprovedCount} summary_rows=${result.monthlySummaryRowCount}`
  );
}
