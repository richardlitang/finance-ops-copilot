from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.domain import EvidenceLink, EvidenceRecord, SourceDocument, SpendingEvent
from app.domain.models import MatchCandidate
from app.orm import EvidenceLinkRow, EvidenceRecordRow, MatchCandidateRow, SourceDocumentRow, SpendingEventRow
from app.orm.mappers import (
    evidence_link_from_row,
    evidence_link_to_row,
    evidence_record_from_row,
    evidence_record_to_row,
    match_candidate_from_row,
    match_candidate_to_row,
    source_document_from_row,
    source_document_to_row,
    spending_event_from_row,
    spending_event_to_row,
)


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
