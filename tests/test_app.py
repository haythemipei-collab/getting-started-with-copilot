import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Save original activities
    original = activities.copy()
    yield
    # Restore original activities after test
    activities.clear()
    activities.update(original)

def test_root_redirect(client):
    """Test that root path redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"

def test_get_activities(client):
    """Test getting the list of activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    # Verify activity structure
    activity = data["Chess Club"]
    assert all(key in activity for key in ["description", "schedule", "max_participants", "participants"])

def test_signup_success(client):
    """Test successful activity signup"""
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in activities[activity_name]["participants"]

def test_signup_duplicate(client):
    """Test signing up an already registered student"""
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already registered in this activity
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()

def test_signup_invalid_activity(client):
    """Test signing up for a non-existent activity"""
    response = client.post("/activities/InvalidActivity/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_unregister_success(client):
    """Test successful unregistration from activity"""
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Known participant
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email not in activities[activity_name]["participants"]

def test_unregister_not_registered(client):
    """Test unregistering a non-registered student"""
    activity_name = "Chess Club"
    email = "nonexistent@mergington.edu"
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 404
    assert "not registered" in response.json()["detail"].lower()

def test_unregister_invalid_activity(client):
    """Test unregistering from a non-existent activity"""
    response = client.delete("/activities/InvalidActivity/unregister?email=test@mergington.edu")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_activity_capacity(client):
    """Test activity capacity limit"""
    activity_name = "Chess Club"
    activity = activities[activity_name]
    initial_count = len(activity["participants"])
    
    # Fill up to max capacity
    for i in range(activity["max_participants"] - initial_count):
        email = f"student{i}@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
    
    # Try to add one more student
    response = client.post(f"/activities/{activity_name}/signup?email=overflow@mergington.edu")
    assert response.status_code == 400
    assert "full" in response.json()["detail"].lower()