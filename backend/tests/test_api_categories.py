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


def test_create_category_rejects_blank_name():
    client = TestClient(create_app())

    response = client.post("/api/categories", json={"name": "   "})

    assert response.status_code == 422


def test_create_and_list_mapping_rules():
    client = TestClient(create_app())
    client.post("/api/categories", json={"name": "Groceries"})

    created = client.post(
        "/api/categories/rules",
        json={
            "pattern": "Aldi",
            "pattern_type": "merchant",
            "category_id": "cat_1",
            "priority": 100,
        },
    )
    listed = client.get("/api/categories/rules")

    assert created.status_code == 200
    assert created.json()["id"] == "rule_1"
    assert created.json()["pattern_type"] == "merchant"
    assert listed.status_code == 200
    assert listed.json()[0]["pattern"] == "Aldi"


def test_create_mapping_rule_rejects_blank_pattern():
    client = TestClient(create_app())
    client.post("/api/categories", json={"name": "Groceries"})

    response = client.post(
        "/api/categories/rules",
        json={
            "pattern": "   ",
            "pattern_type": "merchant",
            "category_id": "cat_1",
        },
    )

    assert response.status_code == 422


def test_create_mapping_rule_rejects_invalid_pattern_type():
    client = TestClient(create_app())
    client.post("/api/categories", json={"name": "Groceries"})

    response = client.post(
        "/api/categories/rules",
        json={
            "pattern": "Aldi",
            "pattern_type": "memo",
            "category_id": "cat_1",
        },
    )

    assert response.status_code == 422


def test_create_mapping_rule_requires_existing_category():
    client = TestClient(create_app())

    response = client.post(
        "/api/categories/rules",
        json={
            "pattern": "Aldi",
            "pattern_type": "merchant",
            "category_id": "cat_missing",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "category not found"
