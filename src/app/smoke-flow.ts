import fs from "node:fs";
import path from "node:path";
import { buildMonthlySummary } from "./monthly-summary-service.js";
import { createRuntime, type CreateRuntimeOptions } from "../cli/runtime.js";
import { runMigrations } from "../infra/db/migrate.js";
import { getSmokeFixtures, getSmokeMappingRules } from "../fixtures/smoke-fixtures.js";
import type { NormalizedEntry } from "../domain/schemas.js";

export type SmokeFlowOptions = CreateRuntimeOptions & {
  logger?: (line: string) => void;
};

export type SmokeFlowResult = {
  dbPath: string;
  importedFixtureCount: number;
  importedEntryCount: number;
  normalizedAutoApprovedCount: number;
  reviewQueueCount: number;
  exactDuplicateCount: number;
  exportedApprovedCount: number;
  exportedReviewQueueCount: number;
  monthlySummaryRowCount: number;
};

function resolveSmokeDbPath(dbPath?: string): string {
  return path.resolve(dbPath ?? ".tmp/finance_ops_smoke.sqlite");
}

function removeIfExists(filePath: string): void {
  if (fs.existsSync(filePath)) {
    fs.rmSync(filePath, { force: true });
  }
}

function formatReviewSummary(entries: NormalizedEntry[]): string {
  const counts = new Map<string, number>();
  for (const entry of entries) {
    for (const reason of entry.reviewReasons) {
      counts.set(reason, (counts.get(reason) ?? 0) + 1);
    }
  }
  return [...counts.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([reason, count]) => `${reason}=${count}`)
    .join(" ");
}

export async function runSmokeFlow(options: SmokeFlowOptions = {}): Promise<SmokeFlowResult> {
  const logger = options.logger ?? (() => {});
  const dbPath = resolveSmokeDbPath(options.dbPath);
  removeIfExists(dbPath);
  removeIfExists(`${dbPath}-wal`);
  removeIfExists(`${dbPath}-shm`);

  runMigrations({ dbPath });
  logger(`migrate ok db=${dbPath}`);

  const runtime = createRuntime({
    ...options,
    dbPath
  });

  try {
    for (const rule of getSmokeMappingRules()) {
      runtime.repos.mappingRuleRepo.upsert(rule);
    }
    logger(`fixtures loaded rules=${getSmokeMappingRules().length} imports=${getSmokeFixtures().length}`);

    let importedEntryCount = 0;
    for (const fixture of getSmokeFixtures()) {
      const entries = await runtime.services.importPipeline.run(fixture.filePath, fixture.sourceHint);
      importedEntryCount += entries.length;
      logger(`import ${fixture.label} entries=${entries.length}`);
    }

    const allEntries = runtime.repos.entryRepo.listAll();
    let normalizedAutoApprovedCount = 0;
    for (const entry of allEntries) {
      if (entry.status === "normalized") {
        runtime.services.reviewService.approveEntry(entry.entryId);
        normalizedAutoApprovedCount += 1;
      }
    }

    const refreshedEntries = runtime.repos.entryRepo.listAll();
    const reviewQueue = runtime.services.reviewService.listQueue();
    const exactDuplicateCount = refreshedEntries.filter(
      (entry) => entry.duplicateCheck.status === "exact_duplicate_import"
    ).length;
    logger(
      `review_queue=${reviewQueue.length} exact_duplicates=${exactDuplicateCount} ${formatReviewSummary(reviewQueue)}`
    );

    const exportedApprovedCount = await runtime.services.sheetsService.syncApprovedEntries(refreshedEntries);
    const exportedReviewQueueCount = await runtime.services.sheetsService.syncReviewQueue(refreshedEntries);
    logger(
      `export approved=${exportedApprovedCount} review_queue=${exportedReviewQueueCount} auto_approved=${normalizedAutoApprovedCount}`
    );

    const summaryRows = buildMonthlySummary(refreshedEntries);
    await runtime.services.sheetsService.syncMonthlySummary(summaryRows);
    logger(`summary rows=${summaryRows.length}`);

    return {
      dbPath,
      importedFixtureCount: getSmokeFixtures().length,
      importedEntryCount,
      normalizedAutoApprovedCount,
      reviewQueueCount: reviewQueue.length,
      exactDuplicateCount,
      exportedApprovedCount,
      exportedReviewQueueCount,
      monthlySummaryRowCount: summaryRows.length
    };
  } finally {
    runtime.db.close();
  }
}
