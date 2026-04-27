from fastapi.testclient import TestClient

from app.main import create_app


def test_summary_endpoint_returns_fast_totals():
    client = TestClient(create_app())
    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )

    response = client.get("/api/summary?month=2026-04&mode=fast")

    assert response.status_code == 200
    body = response.json()
    assert body["total_expense_minor"] == 4297
    assert body["provisional_count"] == 1


def test_export_csv_endpoint_returns_active_events_csv():
    client = TestClient(create_app())
    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )

    response = client.post("/api/export/csv")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "evt_1" in response.text
    assert "confirmation_status" in response.text
