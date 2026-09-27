"""
FitBuddy Celery Configuration & Task Workers
Handles asynchronous background execution of LLM generation tasks.
"""

import os
from celery import Celery
from app.gemini_generator import generate_workout_gemini
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.updated_plan import update_workout_plan

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "fitbuddy_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=120,
)


@celery_app.task(bind=True, name="tasks.generate_full_plan_async")
def generate_full_plan_async(self, name: str, age: int, weight: float, goal: str, intensity: str):
    """Background task orchestrating workout and nutrition plan synthesis."""
    self.update_state(state="PROCESSING", meta={"step": "generating_workout"})
    workout_plan = generate_workout_gemini(name, age, weight, goal, intensity)

    self.update_state(state="PROCESSING", meta={"step": "calculating_nutrition"})
    nutrition_tip = generate_nutrition_tip_with_flash(goal, intensity, weight)

    return {
        "status": "COMPLETED",
        "workout_plan": workout_plan,
        "nutrition_tip": nutrition_tip,
    }


@celery_app.task(name="tasks.update_plan_async")
def update_plan_async(original_plan: str, feedback: str):
    """Background task for single-turn plan revision."""
    revised_plan = update_workout_plan(original_plan, feedback)
    return {
        "status": "COMPLETED",
        "revised_plan": revised_plan,
    }
