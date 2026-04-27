from __future__ import annotations

from app.domain import Category, EvidenceLink, EvidenceRecord, SourceDocument, SpendingEvent
from app.domain.models import MatchCandidate
from app.services.categorization import MappingRule


class InMemoryFinanceRepository:
    def __init__(self) -> None:
        self.source_documents: dict[str, SourceDocument] = {}
        self.evidence_records: dict[str, EvidenceRecord] = {}
        self.spending_events: dict[str, SpendingEvent] = {}
        self.evidence_links: dict[str, EvidenceLink] = {}
        self.match_candidates: dict[str, MatchCandidate] = {}
        self.categories: dict[str, Category] = {}
        self.mapping_rules: dict[str, MappingRule] = {}
        self._source_by_fingerprint: dict[str, str] = {}
        self._evidence_by_fingerprint: dict[str, str] = {}

    def save_source_document(self, source_document: SourceDocument) -> SourceDocument:
        if source_document.fingerprint and source_document.fingerprint in self._source_by_fingerprint:
            return self.source_documents[self._source_by_fingerprint[source_document.fingerprint]]
        self.source_documents[source_document.id] = source_document
        if source_document.fingerprint:
            self._source_by_fingerprint[source_document.fingerprint] = source_document.id
        return source_document

    def save_evidence_record(self, evidence_record: EvidenceRecord) -> EvidenceRecord:
        if evidence_record.fingerprint in self._evidence_by_fingerprint:
            return self.evidence_records[self._evidence_by_fingerprint[evidence_record.fingerprint]]
        self.evidence_records[evidence_record.id] = evidence_record
        self._evidence_by_fingerprint[evidence_record.fingerprint] = evidence_record.id
        return evidence_record

    def save_spending_event(self, spending_event: SpendingEvent) -> SpendingEvent:
        self.spending_events[spending_event.id] = spending_event
        return spending_event

    def save_evidence_link(self, evidence_link: EvidenceLink) -> EvidenceLink:
        self.evidence_links[evidence_link.id] = evidence_link
        return evidence_link

    def save_match_candidate(self, match_candidate: MatchCandidate) -> MatchCandidate:
        self.match_candidates[match_candidate.id] = match_candidate
        return match_candidate

    def save_category(self, category: Category) -> Category:
        self.categories[category.id] = category
        return category

    def save_mapping_rule(self, mapping_rule: MappingRule) -> MappingRule:
        self.mapping_rules[mapping_rule.id] = mapping_rule
        return mapping_rule

    def get_spending_event(self, event_id: str) -> SpendingEvent | None:
        return self.spending_events.get(event_id)

    def get_evidence_record(self, evidence_record_id: str) -> EvidenceRecord | None:
        return self.evidence_records.get(evidence_record_id)

    def get_match_candidate(self, match_candidate_id: str) -> MatchCandidate | None:
        return self.match_candidates.get(match_candidate_id)

    def list_spending_events(self) -> list[SpendingEvent]:
        return list(self.spending_events.values())

    def list_provisional_events(self) -> list[SpendingEvent]:
        return [
            event
            for event in self.spending_events.values()
            if event.confirmation_status.value == "provisional"
        ]

    def find_event_by_canonical_evidence_id(self, evidence_record_id: str) -> SpendingEvent | None:
        for event in self.spending_events.values():
            if event.canonical_source_evidence_id == evidence_record_id:
                return event
        return None

    def evidence_record_exists(self, evidence_record_id: str) -> bool:
        return evidence_record_id in self.evidence_records

    def find_evidence_by_fingerprint(self, fingerprint: str) -> EvidenceRecord | None:
        evidence_id = self._evidence_by_fingerprint.get(fingerprint)
        return self.evidence_records[evidence_id] if evidence_id else None

    def list_match_candidates(self) -> list[MatchCandidate]:
        return list(self.match_candidates.values())

    def list_evidence_links(self) -> list[EvidenceLink]:
        return list(self.evidence_links.values())

    def list_categories(self) -> list[Category]:
        return list(self.categories.values())

    def list_mapping_rules(self) -> list[MappingRule]:
        return sorted(self.mapping_rules.values(), key=lambda rule: rule.priority, reverse=True)

    def next_id(self, entity_name: str) -> str:
        prefixes = {
            "source_document": ("src", self.source_documents),
            "evidence_record": ("ev", self.evidence_records),
            "spending_event": ("evt", self.spending_events),
            "evidence_link": ("link", self.evidence_links),
            "category": ("cat", self.categories),
            "mapping_rule": ("rule", self.mapping_rules),
        }
        prefix, collection = prefixes[entity_name]
        return f"{prefix}_{len(collection) + 1}"
