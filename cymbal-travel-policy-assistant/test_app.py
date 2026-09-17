import pytest
from fastapi.testclient import TestClient
from main import app, agent
from agent import clear_session_history

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "cymbal-travel-policy-agent"

def test_scenario_a_switzerland_meal_cap():
    clear_session_history("test_session_a")
    response = client.post("/chat", json={
        "message": "What is the meal cap for Switzerland?",
        "session_id": "test_session_a"
    })
    assert response.status_code == 200
    data = response.json()
    reply = data["response"]
    assert "120 CHF" in reply or "135" in reply
    assert len(data["retrieved_context"]) > 0

def test_scenario_b_first_class_flight():
    clear_session_history("test_session_b")
    response = client.post("/chat", json={
        "message": "Can I book a first-class flight from Dublin to Zurich?",
        "session_id": "test_session_b"
    })
    assert response.status_code == 200
    data = response.json()
    reply = data["response"].lower()
    assert "no" in reply or "prohibited" in reply or "cannot" in reply or "economy" in reply
    assert "first class" in reply or "6-hour" in reply or "6 hour" in reply or "economy" in reply

def test_scenario_c_hotel_movie():
    clear_session_history("test_session_c")
    response = client.post("/chat", json={
        "message": "Can I buy a movie on the hotel TV?",
        "session_id": "test_session_c"
    })
    assert response.status_code == 200
    data = response.json()
    reply = data["response"].lower()
    assert "non-reimbursable" in reply or "not" in reply or "cannot" in reply or "no" in reply

def test_scenario_d_uncovered_policy_query():
    clear_session_history("test_session_d")
    response = client.post("/chat", json={
        "message": "Can I bring my pet dog on a business trip?",
        "session_id": "test_session_d"
    })
    assert response.status_code == 200
    data = response.json()
    reply = data["response"]
    expected_fallback = "I'm sorry, I cannot find the answer to that in the current Cymbal Group Travel Policy. Please escalate this query to your local HR Business Partner."
    assert expected_fallback in reply

def test_clear_session():
    response = client.post("/clear_session?session_id=test_session_a")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
