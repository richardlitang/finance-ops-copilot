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
