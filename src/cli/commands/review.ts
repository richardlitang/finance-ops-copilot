import { createRuntime } from "../runtime.js";
import type { Category } from "../../domain/enums.js";

export async function runReviewCommand(args: string[]): Promise<void> {
  const sub = args[0] ?? "list";
  const runtime = createRuntime();
  try {
    if (sub === "list") {
      const queue = runtime.services.reviewService.listQueue();
      console.log(`review_queue=${queue.length}`);
      for (const entry of queue) {
        console.log(`${entry.entryId} reasons=${entry.reviewReasons.join("|")}`);
      }
      return;
    }

    const entryId = args[1];
    if (!entryId) {
      throw new Error("usage: review <list|approve|reject|edit-category|mark-duplicate|ignore-duplicate> <entry-id> [arg]");
    }

    if (sub === "approve") {
      runtime.services.reviewService.approveEntry(entryId);
    } else if (sub === "reject") {
      runtime.services.reviewService.rejectMalformed(entryId);
    } else if (sub === "edit-category") {
      const category = args[2] as Category | undefined;
      if (!category) throw new Error("usage: review edit-category <entry-id> <category>");
      runtime.services.reviewService.editCategory(entryId, category);
    } else if (sub === "mark-duplicate") {
      runtime.services.reviewService.markDuplicate(entryId, args[2]);
    } else if (sub === "ignore-duplicate") {
      runtime.services.reviewService.ignoreDuplicateWarning(entryId);
    } else {
      throw new Error(`unknown review subcommand: ${sub}`);
    }

    console.log(`review action applied: ${sub} entry=${entryId}`);
  } finally {
    runtime.db.close();
  }
}
