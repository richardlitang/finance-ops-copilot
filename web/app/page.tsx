"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  apiGet,
  apiPost,
  Category,
  EventEvidence,
  formatMoney,
  ImportResponse,
  MatchCandidate,
  MonthlySummary,
  ReviewActionResponse,
  SpendingEvent,
} from "./lib/api";

type Tab = "imports" | "events" | "review" | "summary";

const sampleReceipt = "ALDI\nDate: 17/04/2026\nTotal: EUR 42.97";
const sampleStatement =
  "date,posted_date,description,merchant,amount,currency\n2026-04-17,2026-04-18,ALDI,ALDI,42.97,EUR";

export default function Home() {
  const [tab, setTab] = useState<Tab>("imports");
  const [month, setMonth] = useState("2026-04");
  const [receiptText, setReceiptText] = useState(sampleReceipt);
  const [statementCsv, setStatementCsv] = useState(sampleStatement);
  const [events, setEvents] = useState<SpendingEvent[]>([]);
  const [matches, setMatches] = useState<MatchCandidate[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [summary, setSummary] = useState<MonthlySummary | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [eventEvidence, setEventEvidence] = useState<EventEvidence | null>(null);
  const [categoryId, setCategoryId] = useState("");
  const [newCategoryName, setNewCategoryName] = useState("Groceries");
  const [createRule, setCreateRule] = useState(true);
  const [activity, setActivity] = useState("Ready");
  const [error, setError] = useState<string | null>(null);

  const selectedEvent = useMemo(
    () => events.find((event) => event.id === selectedEventId) ?? events[0] ?? null,
    [events, selectedEventId],
  );

  useEffect(() => {
    void refreshAll(month);
  }, [month]);

  useEffect(() => {
    if (!selectedEvent) {
      setEventEvidence(null);
      return;
    }
    setSelectedEventId(selectedEvent.id);
    void loadEvidence(selectedEvent.id);
  }, [selectedEvent?.id]);

  async function runAction(label: string, action: () => Promise<void>) {
    setError(null);
    setActivity(label);
    try {
      await action();
      setActivity(`${label} complete`);
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Request failed");
      setActivity("Blocked");
    }
  }

  async function refreshAll(targetMonth = month) {
    await runAction("Refresh", async () => {
      const [nextEvents, nextMatches, nextCategories, nextSummary] = await Promise.all([
        apiGet<SpendingEvent[]>(`/api/events?month=${targetMonth}`),
        apiGet<MatchCandidate[]>("/api/review/matches"),
        apiGet<Category[]>("/api/categories"),
        apiGet<MonthlySummary>(`/api/summary?month=${targetMonth}&mode=fast`),
      ]);
      setEvents(nextEvents);
      setMatches(nextMatches);
      setCategories(nextCategories);
      setSummary(nextSummary);
    });
  }

  async function loadEvidence(eventId: string) {
    try {
      setEventEvidence(await apiGet<EventEvidence>(`/api/events/${eventId}/evidence`));
    } catch {
      setEventEvidence(null);
    }
  }

  async function importReceipt(event: FormEvent) {
    event.preventDefault();
    await runAction("Import receipt", async () => {
      const result = await apiPost<ImportResponse>("/api/imports/receipt-text", {
        raw_text: receiptText,
        filename: "receipt.txt",
      });
      setSelectedEventId(result.spending_event_ids[0] ?? null);
      await refreshAll();
    });
  }

  async function importStatement(event: FormEvent) {
    event.preventDefault();
    await runAction("Import statement", async () => {
      await apiPost<ImportResponse>("/api/imports/statement-csv", {
        raw_csv: statementCsv,
        filename: "statement.csv",
      });
      await refreshAll();
    });
  }

  async function confirmMatch(matchId: string) {
    await runAction("Confirm match", async () => {
      const result = await apiPost<ReviewActionResponse>(`/api/review/matches/${matchId}/confirm`);
      setSelectedEventId(result.spending_event.id);
      await refreshAll();
    });
  }

  async function rejectMatch(matchId: string) {
    await runAction("Reject match", async () => {
      await apiPost(`/api/review/matches/${matchId}/reject`);
      await refreshAll();
    });
  }

  async function confirmManual(eventId: string) {
    await runAction("Confirm manual", async () => {
      await apiPost(`/api/review/events/${eventId}/confirm-manual`);
      await refreshAll();
    });
  }

  async function correctCategory(event: FormEvent) {
    event.preventDefault();
    if (!selectedEvent || !categoryId) {
      return;
    }
    await runAction("Correct category", async () => {
      await apiPost(`/api/review/events/${selectedEvent.id}/category`, {
        category_id: categoryId,
        create_mapping_rule: createRule,
      });
      await refreshAll();
    });
  }

  async function createCategory() {
    const name = newCategoryName.trim();
    if (!name) {
      return;
    }
    await runAction("Create category", async () => {
      const category = await apiPost<Category>("/api/categories", { name });
      setCategoryId(category.id);
      setNewCategoryName("");
      await refreshAll();
    });
  }

  async function exportCsv() {
    await runAction("Export CSV", async () => {
      const response = await fetch("/api/export/csv", { method: "POST" });
      if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `finance-events-${month}.csv`;
      link.click();
      URL.revokeObjectURL(url);
    });
  }

  return (
    <main className="workspace">
      <aside className="rail" aria-label="Primary">
        <div>
          <p className="eyebrow">Finance Ops</p>
          <h1>Reconciliation bench</h1>
        </div>
        <nav className="tabs">
          {(["imports", "events", "review", "summary"] as Tab[]).map((item) => (
            <button
              key={item}
              className={tab === item ? "tab active" : "tab"}
              onClick={() => setTab(item)}
              type="button"
            >
              {item}
            </button>
          ))}
        </nav>
        <div className="railStatus">
          <span className="dot" />
          <span>{activity}</span>
        </div>
        {error ? <p className="errorText">{error}</p> : null}
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Month</p>
            <input
              aria-label="Month"
              className="monthInput"
              onChange={(event) => setMonth(event.target.value)}
              type="month"
              value={month}
            />
          </div>
          <button className="ghostButton" onClick={() => void refreshAll()} type="button">
            Refresh
          </button>
        </header>

        {tab === "imports" ? (
          <ImportsView
            importReceipt={importReceipt}
            importStatement={importStatement}
            receiptText={receiptText}
            setReceiptText={setReceiptText}
            setStatementCsv={setStatementCsv}
            statementCsv={statementCsv}
          />
        ) : null}

        {tab === "events" ? (
          <EventsView
            events={events}
            eventEvidence={eventEvidence}
            onSelect={setSelectedEventId}
            selectedEvent={selectedEvent}
          />
        ) : null}

        {tab === "review" ? (
          <ReviewView
            categories={categories}
            categoryId={categoryId}
            confirmManual={confirmManual}
            confirmMatch={confirmMatch}
            correctCategory={correctCategory}
            createRule={createRule}
            createCategory={createCategory}
            events={events}
            matches={matches}
            newCategoryName={newCategoryName}
            rejectMatch={rejectMatch}
            selectedEvent={selectedEvent}
            setCategoryId={setCategoryId}
            setCreateRule={setCreateRule}
            setNewCategoryName={setNewCategoryName}
            setSelectedEventId={setSelectedEventId}
          />
        ) : null}

        {tab === "summary" ? (
          <SummaryView exportCsv={exportCsv} month={month} summary={summary} />
        ) : null}
      </section>
    </main>
  );
}

function ImportsView(props: {
  importReceipt: (event: FormEvent) => Promise<void>;
  importStatement: (event: FormEvent) => Promise<void>;
  receiptText: string;
  setReceiptText: (value: string) => void;
  setStatementCsv: (value: string) => void;
  statementCsv: string;
}) {
  return (
    <div className="split">
      <form className="panel" onSubmit={(event) => void props.importReceipt(event)}>
        <div className="panelHeader">
          <h2>Receipt text</h2>
          <button type="submit">Import</button>
        </div>
        <textarea
          aria-label="Receipt text"
          value={props.receiptText}
          onChange={(event) => props.setReceiptText(event.target.value)}
        />
      </form>
      <form className="panel" onSubmit={(event) => void props.importStatement(event)}>
        <div className="panelHeader">
          <h2>Statement CSV</h2>
          <button type="submit">Import</button>
        </div>
        <textarea
          aria-label="Statement CSV"
          value={props.statementCsv}
          onChange={(event) => props.setStatementCsv(event.target.value)}
        />
      </form>
    </div>
  );
}

function EventsView(props: {
  events: SpendingEvent[];
  eventEvidence: EventEvidence | null;
  onSelect: (eventId: string) => void;
  selectedEvent: SpendingEvent | null;
}) {
  return (
    <div className="evidenceGrid">
      <div className="panel">
        <div className="panelHeader">
          <h2>Events</h2>
          <span>{props.events.length}</span>
        </div>
        <div className="table">
          {props.events.map((event) => (
            <button
              className={props.selectedEvent?.id === event.id ? "row selected" : "row"}
              key={event.id}
              onClick={() => props.onSelect(event.id)}
              type="button"
            >
              <span>{event.merchant_normalized}</span>
              <span>{formatMoney(event.amount_minor, event.currency)}</span>
              <StatusPill value={event.confirmation_status} />
              <StatusPill value={event.source_quality} />
            </button>
          ))}
        </div>
      </div>
      <EvidencePanel eventEvidence={props.eventEvidence} />
    </div>
  );
}

function ReviewView(props: {
  categories: Category[];
  categoryId: string;
  confirmManual: (eventId: string) => Promise<void>;
  confirmMatch: (matchId: string) => Promise<void>;
  correctCategory: (event: FormEvent) => Promise<void>;
  createCategory: () => Promise<void>;
  createRule: boolean;
  events: SpendingEvent[];
  matches: MatchCandidate[];
  newCategoryName: string;
  rejectMatch: (matchId: string) => Promise<void>;
  selectedEvent: SpendingEvent | null;
  setCategoryId: (value: string) => void;
  setCreateRule: (value: boolean) => void;
  setNewCategoryName: (value: string) => void;
  setSelectedEventId: (value: string) => void;
}) {
  const provisionalEvents = props.events.filter(
    (event) => event.confirmation_status === "provisional",
  );

  return (
    <div className="reviewGrid">
      <div className="panel">
        <div className="panelHeader">
          <h2>Possible matches</h2>
          <span>{props.matches.length}</span>
        </div>
        <div className="stack">
          {props.matches.map((match) => (
            <div className="reviewItem" key={match.id}>
              <div>
                <strong>{match.spending_event_id}</strong>
                <p>{match.reasons.join(", ")}</p>
              </div>
              <span className="score">{match.score}</span>
              <button onClick={() => void props.confirmMatch(match.id)} type="button">
                Confirm
              </button>
              <button className="ghostButton" onClick={() => void props.rejectMatch(match.id)} type="button">
                Reject
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <div className="panelHeader">
          <h2>Receipt-only</h2>
          <span>{provisionalEvents.length}</span>
        </div>
        <div className="stack">
          {provisionalEvents.map((event) => (
            <div className="reviewItem" key={event.id}>
              <button className="plainSelect" onClick={() => props.setSelectedEventId(event.id)} type="button">
                {event.merchant_normalized}
              </button>
              <span>{formatMoney(event.amount_minor, event.currency)}</span>
              <button onClick={() => void props.confirmManual(event.id)} type="button">
                Manual
              </button>
            </div>
          ))}
        </div>
      </div>

      <form className="panel categoryPanel" onSubmit={(event) => void props.correctCategory(event)}>
        <div className="panelHeader">
          <h2>Category</h2>
          <span>{props.selectedEvent?.id ?? "none"}</span>
        </div>
        <select
          aria-label="Category"
          value={props.categoryId}
          onChange={(event) => props.setCategoryId(event.target.value)}
        >
          <option value="">Select category</option>
          {props.categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
        <div className="inlineCreate">
          <input
            aria-label="New category name"
            onChange={(event) => props.setNewCategoryName(event.target.value)}
            placeholder="New category"
            type="text"
            value={props.newCategoryName}
          />
          <button onClick={() => void props.createCategory()} type="button">
            Add
          </button>
        </div>
        <label className="checkLine">
          <input
            checked={props.createRule}
            onChange={(event) => props.setCreateRule(event.target.checked)}
            type="checkbox"
          />
          Create merchant rule
        </label>
        <button disabled={!props.selectedEvent || !props.categoryId} type="submit">
          Apply
        </button>
      </form>
    </div>
  );
}

function EvidencePanel({ eventEvidence }: { eventEvidence: EventEvidence | null }) {
  return (
    <div className="panel">
      <div className="panelHeader">
        <h2>Evidence</h2>
        <span>{eventEvidence?.event.id ?? "none"}</span>
      </div>
      <div className="stack">
        {eventEvidence?.linked_evidence.map((item) => (
          <div className="evidenceItem" key={item.id}>
            <div>
              <strong>{item.evidence.evidence_type}</strong>
              <p>{item.evidence.merchant_normalized ?? item.evidence.description_raw ?? "No label"}</p>
            </div>
            <span>{formatMoney(item.evidence.amount_minor, item.evidence.currency ?? "EUR")}</span>
            <StatusPill value={item.status} />
          </div>
        ))}
        {eventEvidence?.match_candidates.map((candidate) => (
          <div className="matchTrace" key={candidate.id}>
            <span className="score">{candidate.score}</span>
            <p>{candidate.reasons.join(", ")}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function SummaryView({
  exportCsv,
  month,
  summary,
}: {
  exportCsv: () => Promise<void>;
  month: string;
  summary: MonthlySummary | null;
}) {
  return (
    <div className="summaryGrid">
      <div className="panel metricPanel">
        <p className="eyebrow">{month}</p>
        <strong>{formatMoney(summary?.total_expense_minor ?? 0)}</strong>
        <span>{summary?.event_count ?? 0} events</span>
      </div>
      <div className="panel metricPanel">
        <p className="eyebrow">Review</p>
        <strong>{summary?.provisional_count ?? 0}</strong>
        <span>{formatMoney(summary?.category_totals_minor.uncategorized ?? 0)} uncategorized</span>
      </div>
      <div className="panel">
        <div className="panelHeader">
          <h2>Category totals</h2>
          <button onClick={() => void exportCsv()} type="button">
            Export CSV
          </button>
        </div>
        <div className="stack">
          {Object.entries(summary?.category_totals_minor ?? {}).map(([category, amount]) => (
            <div className="summaryLine" key={category}>
              <span>{category}</span>
              <strong>{formatMoney(amount)}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatusPill({ value }: { value: string }) {
  return <span className={`pill ${value.replaceAll("_", "-")}`}>{value.replaceAll("_", " ")}</span>;
}
