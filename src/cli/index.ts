import { runImportCommand } from "./commands/import.js";
import { runReviewCommand } from "./commands/review.js";
import { runExportCommand } from "./commands/export.js";
import { runSummaryCommand } from "./commands/summary.js";
import { runSmokeCommand } from "./commands/smoke.js";

async function main(): Promise<void> {
  const [command, ...rest] = process.argv.slice(2);

  if (!command || command === "--help" || command === "-h") {
    console.log("usage: copilot <import|review|export|summary|smoke> [...args]");
    return;
  }

  if (command === "import") {
    await runImportCommand(rest);
    return;
  }
  if (command === "review") {
    await runReviewCommand(rest);
    return;
  }
  if (command === "export") {
    await runExportCommand();
    return;
  }
  if (command === "summary") {
    await runSummaryCommand();
    return;
  }
  if (command === "smoke") {
    await runSmokeCommand();
    return;
  }

  throw new Error(`unknown command: ${command}`);
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
