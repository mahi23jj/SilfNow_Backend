from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch
import uuid


client = TestClient(app)


def test_routes_endpoint_returns_list(monkeypatch):
    payload = {
        "from_node_id": str(uuid.uuid4()),
        "to_node_id": str(uuid.uuid4()),
        "preference": "balanced",
    }

    fake_result = [
        {
            "path": [payload["from_node_id"], payload["to_node_id"]],
            "total_time": 10.0,
            "total_cost": 5.0,
            "total_risk": 0.2,
            "labels": ["FASTEST"],
            "explanation": [],
        }
    ]

    with patch("app.api.v1.endpoints.routes.compute_routes", return_value=fake_result):
        resp = client.post("/api/v1/routes", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["total_time"] == 10.0
