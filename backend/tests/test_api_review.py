from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.domain import EvidenceRecord, EvidenceType
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


def test_correct_event_category_can_create_future_mapping_rule():
    client = TestClient(create_app())
    client.post("/api/categories", json={"name": "Groceries"})
    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )

    response = client.post(
        "/api/review/events/evt_1/category",
        json={"category_id": "cat_1", "create_mapping_rule": True},
    )
    rules = client.get("/api/categories/rules")

    assert response.status_code == 200
    assert response.json()["spending_event"]["category_id"] == "cat_1"
    assert rules.json()[0]["pattern"] == "Aldi"
    assert rules.json()[0]["created_from_review"] is True


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


def test_confirm_match_updates_event_and_links_statement_evidence():
    app = create_app()
    client = TestClient(app)
    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )
    app.state.repository.save_evidence_record(
        EvidenceRecord(
            id="ev_statement_1",
            source_document_id="src_statement_1",
            evidence_type=EvidenceType.STATEMENT_ROW,
            merchant_normalized="Aldi",
            occurred_at=datetime(2026, 4, 17, tzinfo=timezone.utc),
            posted_at=datetime(2026, 4, 18, tzinfo=timezone.utc),
            amount_minor=4300,
            currency="EUR",
            extraction_confidence=1.0,
            fingerprint="statement-fingerprint",
            created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
        )
    )
    app.state.repository.save_match_candidate(
        MatchCandidate(
            id="match_1",
            spending_event_id="evt_1",
            statement_evidence_record_id="ev_statement_1",
            score=72,
            decision="needs_review",
            reasons=("exact_amount",),
            created_at=datetime(2026, 4, 20, tzinfo=timezone.utc),
        )
    )

    response = client.post("/api/review/matches/match_1/confirm")

    assert response.status_code == 200
    body = response.json()
    assert body["spending_event"]["confirmation_status"] == "confirmed"
    assert body["spending_event"]["amount_minor"] == 4300
    assert body["spending_event"]["source_quality"] == "receipt_and_statement"
    assert body["evidence_link"]["status"] == "confirmed"
