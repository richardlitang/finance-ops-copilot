from fastapi.testclient import TestClient

from app.main import create_app


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
