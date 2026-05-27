import copy

from fastapi.testclient import TestClient
import pytest

from src.app import app, activities

client = TestClient(app)

@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index():
    # Arrange
    expected_title = "Mergington High School"

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert expected_title in response.text


def test_get_activities_returns_available_activities():
    # Arrange
    expected_activities = {"Chess Club", "Programming Class"}

    # Act
    response = client.get("/activities")
    activity_data = response.json()

    # Assert
    assert response.status_code == 200
    assert expected_activities.issubset(activity_data.keys())


def test_signup_for_activity_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "test_student@mergington.edu"
    assert email not in activities[activity_name]["participants"]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_for_unknown_activity_returns_404():
    # Arrange
    unknown_activity = "Unknown%20Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{unknown_activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_for_activity_duplicate_returns_400():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_for_full_activity_returns_400():
    # Arrange
    activity_name = "Math Olympiad"
    email_base = "student{}@mergington.edu"

    # Fill the activity to its max capacity
    activity = activities[activity_name]
    while len(activity["participants"]) < activity["max_participants"]:
        next_email = email_base.format(len(activity["participants"]) + 1)
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": next_email},
        )
        assert response.status_code == 200

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email_base.format(999)},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_from_activity_removes_participant():
    # Arrange
    activity_name = "Programming Class"
    email = "new_student@mergington.edu"
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    assert signup_response.status_code == 200

    # Act
    response = client.post(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_without_signup_returns_400():
    # Arrange
    activity_name = "Chess%20Club"
    email = "missing_student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/unregister",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"
