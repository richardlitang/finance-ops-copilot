from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.domain.models import MatchCandidate
from app.main import create_app


def test_confirm_manual_event_marks_receipt_as_manual_confirmed():
    client = TestClient(create_app())
    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "Cash Cafe\nDate: 17/04/2026\nTotal: €12,00 EUR"},
    )

    response = client.post("/api/review/events/evt_1/confirm-manual")

    assert response.status_code == 200
    body = response.json()["spending_event"]
    assert body["confirmation_status"] == "manual_confirmed"
    assert body["review_status"] == "resolved"
    assert body["source_quality"] == "manual"


def test_confirm_manual_event_returns_404_for_missing_event():
    client = TestClient(create_app())

    response = client.post("/api/review/events/missing/confirm-manual")

    assert response.status_code == 404


def test_mark_event_duplicate_updates_lifecycle_status():
    client = TestClient(create_app())
    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )

    response = client.post("/api/review/events/evt_1/duplicate")

    assert response.status_code == 200
    assert response.json()["spending_event"]["lifecycle_status"] == "duplicate"
    assert response.json()["spending_event"]["review_status"] == "resolved"


def test_ignore_event_updates_lifecycle_status():
    client = TestClient(create_app())
    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )

    response = client.post("/api/review/events/evt_1/ignore")

    assert response.status_code == 200
    assert response.json()["spending_event"]["lifecycle_status"] == "ignored"
    assert response.json()["spending_event"]["review_status"] == "resolved"


def test_list_review_matches_returns_medium_confidence_candidates():
    app = create_app()
    app.state.repository.save_match_candidate(
        MatchCandidate(
            id="match_1",
            spending_event_id="evt_1",
            statement_evidence_record_id="ev_1",
            score=72,
            decision="needs_review",
            reasons=("exact_amount",),
            created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
        )
    )
    client = TestClient(app)

    response = client.get("/api/review/matches")

    assert response.status_code == 200
    assert response.json()[0]["id"] == "match_1"
    assert response.json()[0]["reasons"] == ["exact_amount"]


def test_reject_match_records_rejected_evidence_link():
    app = create_app()
    app.state.repository.save_match_candidate(
        MatchCandidate(
            id="match_1",
            spending_event_id="evt_1",
            statement_evidence_record_id="ev_1",
            score=72,
            decision="needs_review",
            reasons=("exact_amount",),
            created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
        )
    )
    client = TestClient(app)

    response = client.post("/api/review/matches/match_1/reject")

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["spending_event_id"] == "evt_1"
    assert response.json()["evidence_record_id"] == "ev_1"
