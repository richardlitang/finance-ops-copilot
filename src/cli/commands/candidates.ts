import { createRuntime, type CreateRuntimeOptions } from "../runtime.js";

export async function runCandidatesCommand(
  args: string[],
  runtimeOptions: CreateRuntimeOptions = {}
): Promise<void> {
  const scope = args[0];
  const id = args[1];

  if ((scope !== "entry" && scope !== "document") || !id) {
    throw new Error("usage: candidates <entry|document> <id>");
  }

  const runtime = createRuntime(runtimeOptions);
  try {
    const candidates =
      scope === "entry"
        ? runtime.repos.extractedCandidateRepo.listByEntryId(id)
        : runtime.repos.extractedCandidateRepo.listByDocumentId(id);

    console.log(`candidates=${candidates.length} scope=${scope} id=${id}`);
    for (const candidate of candidates) {
      const signals = [
        candidate.merchantRaw ? `merchant=${candidate.merchantRaw}` : null,
        candidate.amountRaw ? `amount=${candidate.amountRaw}` : null,
        candidate.currencyRaw ? `currency=${candidate.currencyRaw}` : null,
        candidate.transactionDateRaw ? `transaction_date=${candidate.transactionDateRaw}` : null,
        candidate.entryId ? `entry=${candidate.entryId}` : null
      ].filter(Boolean);
      console.log(`${candidate.candidateId} ${signals.join(" ")}`.trim());
    }
  } finally {
    runtime.db.close();
  }
}
