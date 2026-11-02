from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True

def test_predict():
    payload = {
        "route_id": "1",
        "direction_id": "Inbound",
        "stop_id": "110",
        "time_point_id": "110",
        "hour": 8,
        "minute_of_day": 490,
        "day_of_week": 1,
        "point_type": "Midpoint",
        "standard_type": "Schedule",
        "scheduled_headway": 12.0,
        "time_point_order": 1.0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "late_probability" in data
    assert "is_late" in data
    assert 0.0 <= data["late_probability"] <= 1.0
