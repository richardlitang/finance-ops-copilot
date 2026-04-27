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
