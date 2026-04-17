import { createRuntime } from "../runtime.js";

export async function runExportCommand(): Promise<void> {
  const runtime = createRuntime();
  try {
    const entries = runtime.repos.entryRepo.listAll();
    const approvedCount = await runtime.services.sheetsService.syncApprovedEntries(entries);
    const reviewCount = await runtime.services.sheetsService.syncReviewQueue(entries);
    console.log(`exported approved=${approvedCount} review_queue=${reviewCount}`);
  } finally {
    runtime.db.close();
  }
}
