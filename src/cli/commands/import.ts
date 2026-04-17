import { createRuntime } from "../runtime.js";

export async function runImportCommand(args: string[]): Promise<void> {
  const target = args[0];
  if (!target) {
    throw new Error("usage: import <file-path> [source-hint]");
  }
  const sourceHint = args[1];
  const runtime = createRuntime();
  try {
    const entries = await runtime.services.importPipeline.run(target, sourceHint);
    console.log(`imported entries=${entries.length}`);
    for (const entry of entries) {
      console.log(`${entry.entryId} status=${entry.status} duplicate=${entry.duplicateCheck.status}`);
    }
  } finally {
    runtime.db.close();
  }
}
