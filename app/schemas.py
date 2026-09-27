from pydantic import BaseModel, Field
from typing import Optional


class UserInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Full Name")
    user_id: str = Field(..., min_length=1, max_length=50, description="Unique User ID / Username")
    age: int = Field(..., ge=10, le=120, description="Age in years")
    weight: float = Field(..., ge=20.0, le=500.0, description="Weight in kg")
    fitness_goal: str = Field(..., description="Target fitness goal e.g. Weight Loss, Muscle Building, Endurance")
    intensity: str = Field(..., description="Workout Intensity: Beginner, Intermediate, Advanced")


class WorkoutRequest(BaseModel):
    name: str
    user_id: str
    age: int
    weight: float
    fitness_goal: str
    intensity: str


class FeedbackRequest(BaseModel):
    user_id: str = Field(..., description="User ID associated with the plan")
    feedback: str = Field(..., min_length=3, description="Feedback or requested modifications")


class WorkoutPlanResponse(BaseModel):
    user_id: str
    original_plan: str
    nutrition_tip: Optional[str] = None
    updated_plan: Optional[str] = None
    feedback: Optional[str] = None

    class Config:
        from_attributes = True
