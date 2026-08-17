from fastapi.testclient import TestClient

from oae.api.app import app


def test_mission_control_landing_page_is_available():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Engineering command center" in response.text
    assert "Start a mission" in response.text
    assert "Missions" in response.text
    assert "Intelligence" in response.text
    assert "Security" in response.text
