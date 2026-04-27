from fastapi.testclient import TestClient

from app.main import create_app


def test_receipt_text_import_endpoint_creates_event():
    client = TestClient(create_app())

    response = client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR", "filename": "aldi.txt"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_document_id"] == "src_1"
    assert body["evidence_record_ids"] == ["ev_1"]
    assert body["spending_event_ids"] == ["evt_1"]
    assert body["evidence_link_ids"] == ["link_1"]


def test_receipt_text_import_endpoint_is_idempotent_for_duplicate_receipts():
    client = TestClient(create_app())
    payload = {"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR", "filename": "aldi.txt"}

    first = client.post("/api/imports/receipt-text", json=payload)
    second = client.post("/api/imports/receipt-text", json=payload)
    events = client.get("/api/events?month=2026-04").json()

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["spending_event_ids"] == ["evt_1"]
    assert second.json()["evidence_link_ids"] == []
    assert len(events) == 1


def test_receipt_text_import_endpoint_applies_mapping_rules():
    client = TestClient(create_app())
    client.post("/api/categories", json={"name": "Groceries"})
    client.post(
        "/api/categories/rules",
        json={
            "pattern": "Aldi",
            "pattern_type": "merchant",
            "category_id": "cat_1",
            "priority": 100,
        },
    )

    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )
    events = client.get("/api/events?month=2026-04").json()

    assert events[0]["category_id"] == "cat_1"


def test_events_endpoint_lists_imported_receipt_event():
    client = TestClient(create_app())
    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )

    response = client.get("/api/events?month=2026-04")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["merchant_normalized"] == "Aldi"
    assert body[0]["confirmation_status"] == "provisional"


def test_event_detail_endpoint_returns_imported_event():
    client = TestClient(create_app())
    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )

    response = client.get("/api/events/evt_1")

    assert response.status_code == 200
    assert response.json()["id"] == "evt_1"
    assert response.json()["merchant_normalized"] == "Aldi"


def test_event_detail_endpoint_returns_404_for_missing_event():
    client = TestClient(create_app())

    response = client.get("/api/events/evt_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "spending event not found"


def test_event_evidence_endpoint_returns_links_evidence_and_match_context():
    client = TestClient(create_app())
    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )

    client.post(
        "/api/imports/statement-csv",
        json={
            "raw_csv": (
                "date,posted_date,description,merchant,amount,currency\n"
                "2026-04-17,2026-04-18,ALDI,ALDI,42.97,EUR"
            )
        },
    )
    response = client.get("/api/events/evt_1/evidence")

    assert response.status_code == 200
    body = response.json()
    assert body["event"]["id"] == "evt_1"
    assert [item["evidence"]["evidence_type"] for item in body["linked_evidence"]] == [
        "receipt",
        "statement_row",
    ]
    assert body["match_candidates"][0]["score"] == 100
    assert set(body["match_candidates"][0]["reasons"]) >= {
        "high_merchant_similarity",
        "exact_amount",
        "same_date",
    }


def test_statement_csv_import_endpoint_confirms_matching_receipt_event():
    client = TestClient(create_app())
    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )

    response = client.post(
        "/api/imports/statement-csv",
        json={
            "raw_csv": (
                "date,posted_date,description,merchant,amount,currency\n"
                "2026-04-17,2026-04-18,ALDI,ALDI,42.97,EUR"
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["match_candidate_ids"] == ["match_ev_2_evt_1"]

    events_response = client.get("/api/events?month=2026-04")
    events = events_response.json()
    assert len(events) == 1
    assert events[0]["confirmation_status"] == "confirmed"
    assert events[0]["source_quality"] == "receipt_and_statement"


def test_statement_csv_import_endpoint_is_idempotent_for_duplicate_statements():
    client = TestClient(create_app())
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
