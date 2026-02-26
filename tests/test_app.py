import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

# create a TestClient once
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: make a deep copy of activities before each test and restore after.

    This fixture runs automatically for every test to ensure tests don't
    interfere with one another by mutating the shared in-memory store.
    """
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_root_redirects_to_static():
    # Arrange
    # client defaults to following redirects; disable it so we can inspect
    # the initial response code and location header.

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in (307, 308)
    assert "/static/index.html" in response.headers["location"]


def test_get_activities_returns_all():
    # Arrange
    expected = copy.deepcopy(activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_signup_for_existing_activity():
    # Arrange
    activity = "Chess Club"
    email = "new@student.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity}"
    assert email in activities[activity]["participants"]


def test_signup_nonexistent_activity_returns_404():
    # Arrange
    activity = "Nonexistent"
    email = "foo@bar.com"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404


def test_signup_duplicate_email_returns_400():
    # Arrange
    activity = "Programming Class"
    email = activities[activity]["participants"][0]

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400


def test_remove_participant_success():
    # Arrange
    activity = "Gym Class"
    email = activities[activity]["participants"][0]

    # Act
    response = client.delete(f"/activities/{activity}/participants", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity}"
    assert email not in activities[activity]["participants"]


def test_remove_from_nonexistent_activity_returns_404():
    # Arrange
    activity = "NotHere"
    email = "someone@nowhere.com"

    # Act
    response = client.delete(f"/activities/{activity}/participants", params={"email": email})

    # Assert
    assert response.status_code == 404


def test_remove_unregistered_email_returns_404():
    # Arrange
    activity = "Music Band"
    email = "absent@domain.com"

    # Act
    response = client.delete(f"/activities/{activity}/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
