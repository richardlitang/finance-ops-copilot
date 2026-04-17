import { createRuntime, type CreateRuntimeOptions } from "../runtime.js";

export async function runImportCommand(
  args: string[],
  runtimeOptions: CreateRuntimeOptions = {}
): Promise<void> {
  const showInspectHints = args.includes("--show");
  const positionalArgs = args.filter((arg) => arg !== "--show");
  const target = positionalArgs[0];
  if (!target) {
    throw new Error("usage: import <file-path> [source-hint] [--show]");
  }
  const sourceHint = positionalArgs[1];
  const runtime = createRuntime(runtimeOptions);
  try {
    const entries = await runtime.services.importPipeline.run(target, sourceHint);
    console.log(`imported entries=${entries.length}`);
    for (const entry of entries) {
      console.log(`${entry.entryId} status=${entry.status} duplicate=${entry.duplicateCheck.status}`);
      if (showInspectHints) {
        console.log(`  inspect normalized: copilot entry show ${entry.entryId}`);
        console.log(`  inspect extracted: copilot candidates entry ${entry.entryId}`);
      }
    }
  } finally {
    runtime.db.close();
  }
}
