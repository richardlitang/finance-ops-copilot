from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.domain import Category, EvidenceLink, EvidenceRecord, SourceDocument, SpendingEvent
from app.domain.models import MatchCandidate
from app.orm import (
    CategoryRow,
    EvidenceLinkRow,
    EvidenceRecordRow,
    MappingRuleRow,
    MatchCandidateRow,
    SourceDocumentRow,
    SpendingEventRow,
)
from app.orm.mappers import (
    category_from_row,
    category_to_row,
    evidence_link_from_row,
    evidence_link_to_row,
    evidence_record_from_row,
    evidence_record_to_row,
    mapping_rule_from_row,
    mapping_rule_to_row,
    match_candidate_from_row,
    match_candidate_to_row,
    source_document_from_row,
    source_document_to_row,
    spending_event_from_row,
    spending_event_to_row,
)
from app.services.categorization import MappingRule


class SqlAlchemyFinanceRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def create_schema(self) -> None:
        bind = self.session_factory.kw["bind"]
        Base.metadata.create_all(bind)

    def save_source_document(self, source_document: SourceDocument) -> SourceDocument:
        with self.session_factory() as session:
            existing = None
            if source_document.fingerprint:
                existing = session.scalars(
                    select(SourceDocumentRow).where(
                        SourceDocumentRow.fingerprint == source_document.fingerprint
                    )
                ).first()
            if existing:
                return source_document_from_row(existing)
            session.merge(source_document_to_row(source_document))
            session.commit()
            return source_document

    def save_evidence_record(self, evidence_record: EvidenceRecord) -> EvidenceRecord:
        with self.session_factory() as session:
            existing = session.scalars(
                select(EvidenceRecordRow).where(
                    EvidenceRecordRow.fingerprint == evidence_record.fingerprint
                )
            ).first()
            if existing:
                return evidence_record_from_row(existing)
            session.merge(evidence_record_to_row(evidence_record))
            session.commit()
            return evidence_record

    def save_spending_event(self, spending_event: SpendingEvent) -> SpendingEvent:
        with self.session_factory() as session:
            session.merge(spending_event_to_row(spending_event))
            session.commit()
            return spending_event

    def save_evidence_link(self, evidence_link: EvidenceLink) -> EvidenceLink:
        with self.session_factory() as session:
            session.merge(evidence_link_to_row(evidence_link))
            session.commit()
            return evidence_link

    def save_match_candidate(self, match_candidate: MatchCandidate) -> MatchCandidate:
        with self.session_factory() as session:
            session.merge(match_candidate_to_row(match_candidate))
            session.commit()
            return match_candidate

    def save_category(self, category: Category) -> Category:
        with self.session_factory() as session:
            session.merge(category_to_row(category))
            session.commit()
            return category

    def save_mapping_rule(self, mapping_rule: MappingRule) -> MappingRule:
        with self.session_factory() as session:
            session.merge(mapping_rule_to_row(mapping_rule))
            session.commit()
            return mapping_rule

    def get_spending_event(self, event_id: str) -> SpendingEvent | None:
        with self.session_factory() as session:
            row = session.get(SpendingEventRow, event_id)
            return spending_event_from_row(row) if row else None

    def get_evidence_record(self, evidence_record_id: str) -> EvidenceRecord | None:
        with self.session_factory() as session:
            row = session.get(EvidenceRecordRow, evidence_record_id)
            return evidence_record_from_row(row) if row else None

    def get_match_candidate(self, match_candidate_id: str) -> MatchCandidate | None:
        with self.session_factory() as session:
            row = session.get(MatchCandidateRow, match_candidate_id)
            return match_candidate_from_row(row) if row else None

    def list_spending_events(self) -> list[SpendingEvent]:
        with self.session_factory() as session:
            rows = session.scalars(select(SpendingEventRow).order_by(SpendingEventRow.occurred_at)).all()
            return [spending_event_from_row(row) for row in rows]

    def list_provisional_events(self) -> list[SpendingEvent]:
        return [
            event
            for event in self.list_spending_events()
            if event.confirmation_status.value == "provisional"
        ]

    def list_evidence_links(self) -> list[EvidenceLink]:
        with self.session_factory() as session:
            rows = session.scalars(select(EvidenceLinkRow).order_by(EvidenceLinkRow.created_at)).all()
            return [evidence_link_from_row(row) for row in rows]

    def list_match_candidates(self) -> list[MatchCandidate]:
        with self.session_factory() as session:
            rows = session.scalars(select(MatchCandidateRow).order_by(MatchCandidateRow.created_at)).all()
            return [match_candidate_from_row(row) for row in rows]

    def list_categories(self) -> list[Category]:
        with self.session_factory() as session:
            rows = session.scalars(select(CategoryRow).order_by(CategoryRow.name)).all()
            return [category_from_row(row) for row in rows]

    def list_mapping_rules(self) -> list[MappingRule]:
        with self.session_factory() as session:
            rows = session.scalars(
                select(MappingRuleRow).order_by(MappingRuleRow.priority.desc())
            ).all()
            return [mapping_rule_from_row(row) for row in rows]

    def find_event_by_canonical_evidence_id(self, evidence_record_id: str) -> SpendingEvent | None:
        with self.session_factory() as session:
            row = session.scalars(
                select(SpendingEventRow).where(
                    SpendingEventRow.canonical_source_evidence_id == evidence_record_id
                )
            ).first()
            return spending_event_from_row(row) if row else None

    def evidence_record_exists(self, evidence_record_id: str) -> bool:
        with self.session_factory() as session:
            return session.get(EvidenceRecordRow, evidence_record_id) is not None

    def find_evidence_by_fingerprint(self, fingerprint: str) -> EvidenceRecord | None:
        with self.session_factory() as session:
            row = session.scalars(
                select(EvidenceRecordRow).where(EvidenceRecordRow.fingerprint == fingerprint)
            ).first()
            return evidence_record_from_row(row) if row else None

    def next_id(self, entity_name: str) -> str:
        mappings = {
            "source_document": ("src", SourceDocumentRow),
            "evidence_record": ("ev", EvidenceRecordRow),
            "spending_event": ("evt", SpendingEventRow),
            "evidence_link": ("link", EvidenceLinkRow),
            "category": ("cat", CategoryRow),
            "mapping_rule": ("rule", MappingRuleRow),
        }
        prefix, row_type = mappings[entity_name]
        with self.session_factory() as session:
            count = session.scalar(select(func.count()).select_from(row_type))
        return f"{prefix}_{(count or 0) + 1}"
