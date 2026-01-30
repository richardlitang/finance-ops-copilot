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


def test_export_google_sheets_endpoint_returns_503_when_gateway_not_configured():
    client = TestClient(create_app())

    response = client.post("/api/export/google-sheets?month=2026-04&mode=fast")

    assert response.status_code == 503
    assert response.json()["detail"] == "google sheets gateway is not configured"


def test_export_google_sheets_endpoint_syncs_rows_through_gateway():
    app = create_app()

    class FakeGateway:
        def __init__(self) -> None:
            self.calls: list[tuple[str, list[dict[str, object]], str]] = []

        def upsert_rows(self, tab: str, rows: list[dict[str, object]], key_field: str) -> None:
            self.calls.append((tab, rows, key_field))

    app.state.sheets_gateway = FakeGateway()
    client = TestClient(app)
    client.post(
        "/api/categories",
        json={"name": "Groceries"},
    )
    client.post(
        "/api/imports/receipt-text",
        json={"raw_text": "ALDI\nDate: 17/04/2026\nTotal: €42,97 EUR"},
    )
    client.post(
        "/api/review/events/evt_1/category",
        json={"category_id": "cat_1", "create_mapping_rule": True},
    )
    client.post(
        "/api/review/events/evt_1/confirm-manual",
    )

    response = client.post("/api/export/google-sheets?month=2026-04&mode=fast")

    assert response.status_code == 200
    assert response.json()["normalized_entries"] == 1
    assert response.json()["mapping_rules"] == 1
    called_tabs = {tab for tab, _, _ in app.state.sheets_gateway.calls}
    assert "normalized_entries" in called_tabs
    assert "mapping_rules" in called_tabs
    assert "monthly_summary" in called_tabs
