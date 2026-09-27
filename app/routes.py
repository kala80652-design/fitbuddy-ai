from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db, save_user, save_plan, update_plan, get_original_plan, get_user, User, WorkoutPlan
from app.schemas import UserInput, WorkoutRequest, FeedbackRequest
from app.gemini_generator import generate_workout_plan
from app.gemini_flash_generator import generate_nutrition_tip
from app.updated_plan import update_workout_plan

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# -------------------------------------------------------------
# Web HTML Routes
# -------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(
    request: Request,
    name: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    fitness_goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Save or update user profile
    user = save_user(
        db=db,
        name=name.strip(),
        user_id=user_id.strip(),
        age=age,
        weight=weight,
        fitness_goal=fitness_goal,
        intensity=intensity
    )

    # 2. Generate Plan & Nutrition Tips via Gemini
    workout_plan_text = generate_workout_plan(
        name=name,
        age=age,
        weight=weight,
        fitness_goal=fitness_goal,
        intensity=intensity
    )

    nutrition_tip_text = generate_nutrition_tip(
        fitness_goal=fitness_goal,
        intensity=intensity,
        weight=weight
    )

    # 3. Save Workout Plan to Database
    plan = save_plan(
        db=db,
        user_id=user.user_id,
        original_plan=workout_plan_text,
        nutrition_tip=nutrition_tip_text
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={"user": user, "plan": plan}
    )


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_user(db, user_id=user_id.strip())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_plan = get_original_plan(db, user_id=user_id.strip())
    if not existing_plan:
        raise HTTPException(status_code=404, detail="No workout plan found for this user")

    # Call Gemini to revise the plan based on original plan + feedback
    revised_plan_text = update_workout_plan(
        original_plan=existing_plan.original_plan,
        feedback=feedback.strip()
    )

    # Update database record
    updated_plan_record = update_plan(
        db=db,
        user_id=user_id.strip(),
        updated_plan=revised_plan_text,
        feedback=feedback.strip()
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "user": user,
            "plan": updated_plan_record,
            "feedback_submitted": True
        }
    )


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={"users": users}
    )


@router.get("/coach-dashboard", response_class=HTMLResponse)
def coach_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="coach_dashboard.html", context={})


@router.get("/corporate-dashboard", response_class=HTMLResponse)
def corporate_dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="corporate_dashboard.html", context={})


@router.get("/live-workout", response_class=HTMLResponse)
def live_workout(request: Request):
    return templates.TemplateResponse(request=request, name="live_workout.html", context={})


# -------------------------------------------------------------
# REST API Endpoints (JSON)
# -------------------------------------------------------------

@router.post("/api/generate-workout")
def api_generate_workout(data: WorkoutRequest, db: Session = Depends(get_db)):
    user = save_user(
        db=db,
        name=data.name.strip(),
        user_id=data.user_id.strip(),
        age=data.age,
        weight=data.weight,
        fitness_goal=data.fitness_goal,
        intensity=data.intensity
    )

    workout_plan_text = generate_workout_plan(
        name=data.name,
        age=data.age,
        weight=data.weight,
        fitness_goal=data.fitness_goal,
        intensity=data.intensity
    )

    nutrition_tip_text = generate_nutrition_tip(
        fitness_goal=data.fitness_goal,
        intensity=data.intensity,
        weight=data.weight
    )

    plan = save_plan(
        db=db,
        user_id=user.user_id,
        original_plan=workout_plan_text,
        nutrition_tip=nutrition_tip_text
    )

    return {
        "status": "success",
        "user": {
            "name": user.name,
            "user_id": user.user_id,
            "age": user.age,
            "weight": user.weight,
            "fitness_goal": user.fitness_goal,
            "intensity": user.intensity
        },
        "plan": {
            "original_plan": plan.original_plan,
            "nutrition_tip": plan.nutrition_tip
        }
    }


@router.post("/api/submit-feedback")
def api_submit_feedback(data: FeedbackRequest, db: Session = Depends(get_db)):
    user = get_user(db, user_id=data.user_id.strip())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing_plan = get_original_plan(db, user_id=data.user_id.strip())
    if not existing_plan:
        raise HTTPException(status_code=404, detail="Workout plan not found")

    revised_plan_text = update_workout_plan(
        original_plan=existing_plan.original_plan,
        feedback=data.feedback.strip()
    )

    updated_plan_record = update_plan(
        db=db,
        user_id=data.user_id.strip(),
        updated_plan=revised_plan_text,
        feedback=data.feedback.strip()
    )

    return {
        "status": "success",
        "user_id": updated_plan_record.user_id,
        "updated_plan": updated_plan_record.updated_plan,
        "feedback": updated_plan_record.feedback
    }


@router.get("/api/users")
def api_get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    results = []
    for u in users:
        plan = u.workout_plans[0] if u.workout_plans else None
        results.append({
            "id": u.id,
            "user_id": u.user_id,
            "name": u.name,
            "age": u.age,
            "weight": u.weight,
            "fitness_goal": u.fitness_goal,
            "intensity": u.intensity,
            "has_plan": plan is not None,
            "has_updated_plan": bool(plan and plan.updated_plan)
        })
    return {"users": results}
