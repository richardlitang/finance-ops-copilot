from fastapi.testclient import TestClient

from app.main import create_app


def test_create_and_list_categories():
    client = TestClient(create_app())

    created = client.post("/api/categories", json={"name": "Groceries"})
    listed = client.get("/api/categories")

    assert created.status_code == 200
    assert created.json()["id"] == "cat_1"
    assert listed.status_code == 200
    assert listed.json()[0]["name"] == "Groceries"
