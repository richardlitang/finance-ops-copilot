import { createRuntime, type CreateRuntimeOptions } from "../runtime.js";

export async function runEntryCommand(
  args: string[],
  runtimeOptions: CreateRuntimeOptions = {}
): Promise<void> {
  const sub = args[0];
  const entryId = args[1];

  if (sub !== "show" || !entryId) {
    throw new Error("usage: entry show <entry-id>");
  }

  const runtime = createRuntime(runtimeOptions);
  try {
    const entry = runtime.repos.entryRepo.findById(entryId);
    if (!entry) {
      throw new Error(`entry not found: ${entryId}`);
    }

    console.log(`entry=${entry.entryId} status=${entry.status} duplicate=${entry.duplicateCheck.status}`);

    const detailSignals = [
      `source_type=${entry.sourceDocument.sourceType}`,
      entry.merchantNormalized ? `merchant=${entry.merchantNormalized}` : entry.merchantRaw ? `merchant=${entry.merchantRaw}` : null,
      `amount=${entry.amount}`,
      `currency=${entry.currency}`,
      entry.transactionDate ? `transaction_date=${entry.transactionDate}` : null,
      entry.postingDate ? `posting_date=${entry.postingDate}` : null,
      `category=${entry.categoryDecision.finalCategory ?? entry.categoryDecision.suggestedCategory}`
    ].filter(Boolean);
    console.log(detailSignals.join(" "));

    if (entry.reviewReasons.length > 0) {
      console.log(`review_reasons=${entry.reviewReasons.join("|")}`);
    }
  } finally {
    runtime.db.close();
  }
}
