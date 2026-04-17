import { z } from "zod";
import {
  AUDIT_EVENT_TYPES,
  CATEGORY_VALUES,
  DUPLICATE_STATUSES,
  ENTRY_STATUSES,
  REVIEW_REASONS,
  SOURCE_TYPES,
  SUGGESTION_SOURCES
} from "./enums.js";

const isoDatetimeSchema = z.string().datetime({ offset: true });
const isoDateSchema = z.string().regex(/^\d{4}-\d{2}-\d{2}$/);
const currencySchema = z.string().length(3).toUpperCase();
const confidenceSchema = z.number().min(0).max(1);

export const sourceDocumentRefSchema = z.object({
  documentId: z.string().min(1),
  sourceType: z.enum(SOURCE_TYPES),
  filename: z.string().min(1),
  mimeType: z.string().min(1),
  importedAt: isoDatetimeSchema,
  localeHint: z.string().min(2).optional(),
  countryHint: z.string().min(2).optional()
});
export type SourceDocumentRef = z.infer<typeof sourceDocumentRefSchema>;

export const extractionMetaSchema = z.object({
  extractorVersion: z.string().min(1),
  rawText: z.string().optional(),
  rawRowJson: z.string().optional(),
  confidence: confidenceSchema,
  warnings: z.array(z.string()).default([])
});
export type ExtractionMeta = z.infer<typeof extractionMetaSchema>;

const lineItemSchema = z.object({
  description: z.string().min(1),
  amount: z.number().optional()
});

export const extractedCandidateSchema = z.object({
  candidateId: z.string().min(1),
  documentId: z.string().min(1),
  sourceType: z.enum(SOURCE_TYPES),
  entryId: z.string().min(1).optional(),
  merchantRaw: z.string().optional(),
  descriptionRaw: z.string().optional(),
  referenceRaw: z.string().optional(),
  transactionDateRaw: z.string().optional(),
  postingDateRaw: z.string().optional(),
  amountRaw: z.string().optional(),
  currencyRaw: z.string().optional(),
  taxAmountRaw: z.string().optional(),
  lineItems: z.array(lineItemSchema).default([]),
  confidence: confidenceSchema,
  warnings: z.array(z.string()).default([]),
  rawText: z.string().optional(),
  rawRowJson: z.string().optional(),
  extractorVersion: z.string().min(1),
  createdAt: isoDatetimeSchema
});
export type ExtractedCandidate = z.infer<typeof extractedCandidateSchema>;

export const categoryDecisionSchema = z.object({
  suggestedCategory: z.enum(CATEGORY_VALUES),
  confidence: confidenceSchema,
  source: z.enum(SUGGESTION_SOURCES),
  rationale: z.string().optional(),
  finalCategory: z.enum(CATEGORY_VALUES).optional()
});
export type CategoryDecision = z.infer<typeof categoryDecisionSchema>;

export const duplicateCheckResultSchema = z.object({
  status: z.enum(DUPLICATE_STATUSES),
  confidence: confidenceSchema,
  relatedEntryId: z.string().optional(),
  signals: z.array(z.string()).default([])
});
export type DuplicateCheckResult = z.infer<typeof duplicateCheckResultSchema>;

export const mappingRuleSchema = z.object({
  ruleId: z.string().min(1),
  field: z.enum(["merchant", "description", "line_item"]),
  pattern: z.string().min(1),
  targetCategory: z.enum(CATEGORY_VALUES),
  priority: z.number().int().min(0),
  createdBy: z.enum(["system", "user"]),
  createdAt: isoDatetimeSchema
});
export type MappingRule = z.infer<typeof mappingRuleSchema>;

export const auditEventSchema = z.object({
  eventId: z.string().min(1),
  entryId: z.string().min(1),
  eventType: z.enum(AUDIT_EVENT_TYPES),
  eventAt: isoDatetimeSchema,
  actor: z.enum(["system", "user"]).default("system"),
  payloadJson: z.string()
});
export type AuditEvent = z.infer<typeof auditEventSchema>;

export const normalizedEntrySchema = z
  .object({
    entryId: z.string().min(1),
    sourceDocument: sourceDocumentRefSchema,
    merchantRaw: z.string().optional(),
    merchantNormalized: z.string().optional(),
    description: z.string().optional(),
    reference: z.string().optional(),
    transactionDate: isoDateSchema.optional(),
    postingDate: isoDateSchema.optional(),
    amount: z.number(),
    currency: currencySchema,
    baseAmount: z.number().optional(),
    baseCurrency: currencySchema.optional(),
    taxAmount: z.number().optional(),
    lineItems: z.array(lineItemSchema).default([]),
    categoryDecision: categoryDecisionSchema,
    duplicateCheck: duplicateCheckResultSchema,
    status: z.enum(ENTRY_STATUSES),
    reviewReasons: z.array(z.enum(REVIEW_REASONS)).default([]),
    extractionMeta: extractionMetaSchema,
    createdAt: isoDatetimeSchema,
    updatedAt: isoDatetimeSchema
  })
  .superRefine((value, ctx) => {
    if (value.status === "approved" && value.duplicateCheck.status === "exact_duplicate_import") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["status"],
        message: "approved status is invalid for exact duplicate imports"
      });
    }
  });
export type NormalizedEntry = z.infer<typeof normalizedEntrySchema>;
