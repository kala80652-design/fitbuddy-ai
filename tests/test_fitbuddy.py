import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import ValidationError

from app.database import Base, get_db, save_user, save_plan, update_plan, get_original_plan, get_user, User, WorkoutPlan
from app.main import app
from app.schemas import UserInput, WorkoutRequest, FeedbackRequest

from sqlalchemy.pool import StaticPool

# Test in-memory SQLite database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Pydantic Schema Validation Tests
# ---------------------------------------------------------------------------

def test_user_input_valid():
    user = UserInput(
        name="Sarah Connor",
        user_id="sarah_c",
        age=30,
        weight=65.5,
        fitness_goal="Strength & Power",
        intensity="Advanced"
    )
    assert user.name == "Sarah Connor"
    assert user.age == 30
    assert user.weight == 65.5


def test_user_input_invalid_age():
    with pytest.raises(ValidationError):
        UserInput(
            name="Invalid User",
            user_id="inv_user",
            age=-5,  # Should fail validation (ge=10)
            weight=70.0,
            fitness_goal="Fat Loss",
            intensity="Beginner"
        )


def test_user_input_invalid_weight():
    with pytest.raises(ValidationError):
        UserInput(
            name="Invalid User",
            user_id="inv_user",
            age=25,
            weight=-10.0,  # Should fail validation (ge=20.0)
            fitness_goal="Fat Loss",
            intensity="Beginner"
        )


def test_feedback_request_validation():
    with pytest.raises(ValidationError):
        FeedbackRequest(
            user_id="user1",
            feedback="hi"  # Too short (min_length=3)
        )


# ---------------------------------------------------------------------------
# 2. Database CRUD Unit Tests
# ---------------------------------------------------------------------------

def test_database_crud_operations():
    db = TestingSessionLocal()
    try:
        # Create user
        user = save_user(
            db=db,
            name="Mark Vance",
            user_id="mark_v",
            age=29,
            weight=82.0,
            fitness_goal="Muscle Building",
            intensity="Intermediate"
        )
        assert user.id is not None
        assert user.user_id == "mark_v"

        # Query user
        queried_user = get_user(db, "mark_v")
        assert queried_user is not None
        assert queried_user.name == "Mark Vance"

        # Save Plan
        plan = save_plan(
            db=db,
            user_id="mark_v",
            original_plan="Day 1: Chest & Triceps\nDay 2: Back & Biceps",
            nutrition_tip="Eat 160g protein daily."
        )
        assert plan.id is not None
        assert plan.original_plan.startswith("Day 1: Chest")

        # Update Plan with Feedback
        updated = update_plan(
            db=db,
            user_id="mark_v",
            updated_plan="Day 1: Upper Body Strength\nDay 2: Lower Body",
            feedback="Replace split with Upper/Lower."
        )
        assert updated.updated_plan.startswith("Day 1: Upper Body")
        assert updated.feedback == "Replace split with Upper/Lower."

        # Verify original plan is retained intact
        retrieved_plan = get_original_plan(db, "mark_v")
        assert retrieved_plan.original_plan.startswith("Day 1: Chest")
        assert retrieved_plan.updated_plan.startswith("Day 1: Upper Body")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 3. Route & Web Integration Tests (Mocking Gemini API)
# ---------------------------------------------------------------------------

def test_get_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "FitBuddy" in response.text
    assert "Generate My 7-Day Plan" in response.text


def test_get_healthz_route(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert "gemini_api_configured" in data


@patch("app.gemini_generator.genai.GenerativeModel")
@patch("app.gemini_flash_generator.genai.GenerativeModel")
def test_post_generate_workout_route(mock_flash_model, mock_workout_model, client):
    from unittest.mock import MagicMock
    mock_workout = MagicMock()
    mock_workout.text = "Day 1: Full Body Strength\n- Squats: 3x10\n- Bench Press: 3x10"
    mock_flash = MagicMock()
    mock_flash.text = "Drink 3.5L of water and consume 140g protein."

    mock_workout_model.return_value.generate_content.return_value = mock_workout
    mock_flash_model.return_value.generate_content.return_value = mock_flash

    payload = {
        "name": "Jane Miller",
        "user_id": "jane_m",
        "age": 27,
        "weight": 62.5,
        "fitness_goal": "Fat Loss & Calorie Burn",
        "intensity": "Intermediate"
    }

    response = client.post("/generate-workout", data=payload)
    assert response.status_code == 200
    assert "Jane Miller" in response.text
    assert "@jane_m" in response.text
    assert "Day 1: Full Body Strength" in response.text
    assert "Drink 3.5L of water" in response.text


@patch("app.updated_plan.genai.GenerativeModel")
def test_post_submit_feedback_route(mock_update_model, client):
    db = TestingSessionLocal()
    try:
        save_user(
            db=db,
            name="John Doe",
            user_id="john_d",
            age=32,
            weight=78.0,
            fitness_goal="Strength & Power",
            intensity="Advanced"
        )
        save_plan(
            db=db,
            user_id="john_d",
            original_plan="Day 1: Barbell Squats 5x5",
            nutrition_tip="Focus on complex carbs."
        )
    finally:
        db.close()

    # Mock revised response
    mock_update_instance = mock_update_model.return_value
    mock_update_instance.generate_content.return_value.text = "Day 1: Dumbbell Goblet Squats 4x12 (Replaced due to back pain)"

    feedback_payload = {
        "user_id": "john_d",
        "feedback": "Replace barbell squats with dumbbell variations"
    }

    response = client.post("/submit-feedback", data=feedback_payload)
    assert response.status_code == 200
    assert "Revised 7-Day Workout Plan" in response.text
    assert "Dumbbell Goblet Squats" in response.text
    assert "Barbell Squats 5x5" in response.text  # Original plan is also rendered


def test_view_all_users_route(client):
    db = TestingSessionLocal()
    try:
        save_user(
            db=db,
            name="Admin Test User",
            user_id="admin_user_01",
            age=24,
            weight=70.0,
            fitness_goal="Cardiovascular Endurance",
            intensity="Beginner"
        )
        save_plan(
            db=db,
            user_id="admin_user_01",
            original_plan="Day 1: 30 min light jog",
            nutrition_tip="Electrolytes after runs."
        )
    finally:
        db.close()

    response = client.get("/view-all-users")
    assert response.status_code == 200
    assert "Admin Test User" in response.text
    assert "@admin_user_01" in response.text
    assert "Day 1: 30 min light jog" in response.text


# ---------------------------------------------------------------------------
# 4. REST API Endpoint Tests
# ---------------------------------------------------------------------------

@patch("app.gemini_generator.genai.GenerativeModel")
@patch("app.gemini_flash_generator.genai.GenerativeModel")
def test_rest_api_endpoints(mock_flash_model, mock_workout_model, client):
    mock_workout_model.return_value.generate_content.return_value.text = "Day 1: Push Routine"
    mock_flash_model.return_value.generate_content.return_value.text = "Eat clean whole foods."

    request_data = {
        "name": "API User",
        "user_id": "api_user_1",
        "age": 28,
        "weight": 75.0,
        "fitness_goal": "Muscle Building & Hypertrophy",
        "intensity": "Intermediate"
    }

    # Test POST /api/generate-workout
    res = client.post("/api/generate-workout", json=request_data)
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["status"] == "success"
    assert res_json["user"]["user_id"] == "api_user_1"

    # Test GET /api/users
    res_users = client.get("/api/users")
    assert res_users.status_code == 200
    users_data = res_users.json()
    assert len(users_data["users"]) >= 1
    assert any(u["user_id"] == "api_user_1" for u in users_data["users"])
