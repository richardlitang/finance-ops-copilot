from datetime import datetime, timezone

from app.domain.models import MatchCandidate
from app.schemas.review import MatchCandidateResponse


def test_match_candidate_response_serializes_reasons_as_list():
    candidate = MatchCandidate(
        id="match_1",
        spending_event_id="evt_1",
        statement_evidence_record_id="ev_1",
        score=72,
        decision="needs_review",
        reasons=("exact_amount", "same_currency"),
        created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
    )

    response = MatchCandidateResponse.from_domain(candidate)

    assert response.reasons == ["exact_amount", "same_currency"]
