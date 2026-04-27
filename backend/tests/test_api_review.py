from fastapi.testclient import TestClient

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
