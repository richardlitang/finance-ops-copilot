export type SpendingEvent = {
  id: string;
  occurred_at: string;
  posted_at: string | null;
  merchant_normalized: string;
  amount_minor: number;
  currency: string;
  direction: string;
  category_id: string | null;
  confirmation_status: string;
  review_status: string;
  lifecycle_status: string;
  source_quality: string;
  canonical_source_evidence_id: string | null;
};

export type ImportResponse = {
  source_document_id: string;
  evidence_record_ids: string[];
  spending_event_ids: string[];
  evidence_link_ids: string[];
  match_candidate_ids: string[];
};

export type MatchCandidate = {
  id: string;
  spending_event_id: string;
  statement_evidence_record_id: string;
  score: number;
  decision: string;
  reasons: string[];
  created_at: string;
};

export type ReviewActionResponse = {
  spending_event: SpendingEvent;
  evidence_link?: {
    id: string;
    spending_event_id: string;
    evidence_record_id: string;
    link_type: string;
    status: string;
    match_score: number | null;
    created_at: string;
  } | null;
};

export type Category = {
  id: string;
  name: string;
  created_at: string;
};

export type EventEvidence = {
  event: SpendingEvent;
  linked_evidence: Array<{
    id: string;
    link_type: string;
    status: string;
    match_score: number | null;
    created_at: string;
    evidence: {
      id: string;
      source_document_id: string;
      evidence_type: string;
      merchant_raw: string | null;
      merchant_normalized: string | null;
      occurred_at: string | null;
      posted_at: string | null;
      amount_minor: number | null;
      currency: string | null;
      description_raw: string | null;
      extraction_confidence: number;
      warnings: string[];
      created_at: string;
    };
  }>;
  match_candidates: Array<{
    id: string;
    statement_evidence_record_id: string;
    score: number;
    decision: string;
    reasons: string[];
    created_at: string;
  }>;
};

export type MonthlySummary = {
  month: string;
  mode: string;
  event_count: number;
  total_expense_minor: number;
  category_totals_minor: Record<string, number>;
  provisional_count: number;
};

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(path, { cache: "no-store" });
  return readResponse<T>(response);
}

export async function apiPost<T>(path: string, payload?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: payload === undefined ? undefined : JSON.stringify(payload),
  });
  return readResponse<T>(response);
}

export function formatMoney(amountMinor: number | null | undefined, currency = "EUR") {
  if (amountMinor === null || amountMinor === undefined) {
    return "n/a";
  }
  return new Intl.NumberFormat("en", {
    style: "currency",
    currency,
  }).format(amountMinor / 100);
}

async function readResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return (await response.json()) as T;
  }

  const fallback = `${response.status} ${response.statusText}`;
  try {
    const body = (await response.json()) as { detail?: string };
    throw new Error(body.detail ?? fallback);
  } catch (error) {
    if (error instanceof Error && error.message !== fallback) {
      throw error;
    }
    throw new Error(fallback);
  }
}
