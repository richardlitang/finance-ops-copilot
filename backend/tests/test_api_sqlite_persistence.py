from fastapi.testclient import TestClient

from app.domain import EvidenceRecord, EvidenceType
from app.domain.models import MatchCandidate
from app.main import create_app
from datetime import datetime, timezone


def test_api_receipt_and_statement_flow_works_with_sqlite_repository(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'finance.sqlite'}"
    client = TestClient(create_app(database_url))

    receipt_response = client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )
    statement_response = client.post(
        "/api/imports/statement-csv",
        json={
            "raw_csv": (
                "date,posted_date,description,merchant,amount,currency\n"
                "2026-04-17,2026-04-18,ALDI,ALDI,42.97,EUR"
            )
        },
    )
    events_response = client.get("/api/events?month=2026-04")

    assert receipt_response.status_code == 200
    assert statement_response.status_code == 200
    events = events_response.json()
    assert len(events) == 1
    assert events[0]["confirmation_status"] == "confirmed"
    assert events[0]["source_quality"] == "receipt_and_statement"


def test_duplicate_receipt_import_does_not_duplicate_sqlite_events(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'finance.sqlite'}"
    client = TestClient(create_app(database_url))
    payload = {"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"}

    first = client.post("/api/imports/receipt-text", json=payload)
    second = client.post("/api/imports/receipt-text", json=payload)
    events = client.get("/api/events?month=2026-04").json()

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["spending_event_ids"] == ["evt_1"]
    assert second.json()["evidence_link_ids"] == []
    assert len(events) == 1


def test_duplicate_statement_import_does_not_duplicate_sqlite_events(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'finance.sqlite'}"
    client = TestClient(create_app(database_url))
    payload = {
        "raw_csv": (
            "date,posted_date,description,merchant,amount,currency\n"
            "2026-04-19,2026-04-20,Netflix,Netflix,15.99,EUR"
        )
    }

    first = client.post("/api/imports/statement-csv", json=payload)
    second = client.post("/api/imports/statement-csv", json=payload)
    events = client.get("/api/events?month=2026-04").json()

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["spending_event_ids"] == []
    assert second.json()["evidence_link_ids"] == []
    assert second.json()["match_candidate_ids"] == []
    assert len(events) == 1


def test_review_actions_work_with_sqlite_repository(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'finance.sqlite'}"
    app = create_app(database_url)
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
            fingerprint="sqlite-statement-fingerprint",
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

    matches = client.get("/api/review/matches")
    confirmed = client.post("/api/review/matches/match_1/confirm")

    assert matches.status_code == 200
    assert matches.json()[0]["id"] == "match_1"
    assert confirmed.status_code == 200
    assert confirmed.json()["spending_event"]["confirmation_status"] == "confirmed"
    assert confirmed.json()["evidence_link"]["status"] == "confirmed"


def test_category_rules_persist_with_sqlite_repository(tmp_path):
    database_url = f"sqlite+pysqlite:///{tmp_path / 'finance.sqlite'}"
    first_client = TestClient(create_app(database_url))

    category_response = first_client.post("/api/categories", json={"name": "Groceries"})
    rule_response = first_client.post(
        "/api/categories/rules",
        json={
            "pattern": "Aldi",
            "pattern_type": "merchant",
            "category_id": "cat_1",
        },
    )

    second_client = TestClient(create_app(database_url))
    categories_response = second_client.get("/api/categories")
    rules_response = second_client.get("/api/categories/rules")

    assert category_response.status_code == 200
    assert rule_response.status_code == 200
    assert categories_response.status_code == 200
    assert rules_response.status_code == 200
    assert categories_response.json()[0]["name"] == "Groceries"
    assert rules_response.json()[0]["category_id"] == "cat_1"
