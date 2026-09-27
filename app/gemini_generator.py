import os
from typing import Union
from dotenv import load_dotenv
import google.generativeai as genai
from app.schemas import UserInput, WorkoutRequest

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


def generate_workout_gemini(user_input: Union[UserInput, WorkoutRequest, dict]) -> str:
    """
    Generates a structured 7-day personalized workout plan using Google Gemini API.
    Accepts UserInput schema, WorkoutRequest, or dict.
    """
    if isinstance(user_input, (UserInput, WorkoutRequest)):
        name = user_input.name
        age = user_input.age
        weight = user_input.weight
        fitness_goal = user_input.fitness_goal
        intensity = user_input.intensity
    elif isinstance(user_input, dict):
        name = user_input.get("name", "User")
        age = user_input.get("age", 25)
        weight = user_input.get("weight", 70)
        fitness_goal = user_input.get("fitness_goal", "General Fitness")
        intensity = user_input.get("intensity", "Intermediate")
    else:
        return "Invalid input format for workout generation."

    prompt = f"""
You are FitBuddy, an elite personal fitness trainer and exercise physiologist.
Create a highly structured, comprehensive, and realistic 7-Day Workout Plan tailored specifically for:

- Client Name: {name}
- Age: {age} years old
- Current Body Weight: {weight} kg
- Primary Fitness Goal: {fitness_goal}
- Experience & Workout Intensity Level: {intensity}

Requirements:
1. Provide a detailed schedule from Day 1 to Day 7. Include appropriate active recovery / rest days based on intensity ({intensity}).
2. For every workout day, clearly format with:
   - Day Title & Focus (e.g., Day 1: Upper Body Strength & Hypertrophy)
   - Warm-up (5–10 mins): Specific dynamic stretches and activation exercises.
   - Main Workout: List each exercise, targeting muscle groups, exact sets, reps (or duration), and recommended rest periods between sets.
   - Cooldown (5–10 mins): Specific static stretching and breathing routines.
3. Add safety notes, form cues, and intensity guidelines suitable for someone who is {age} years old weighing {weight} kg.
4. Keep the output clean, highly readable, organized, and motivating.
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
    except Exception:
        pass

    # Fallback plan when API key is unconfigured or network is unavailable
    return f"""[Notice: Running in Offline/Demo Mode. Add your GOOGLE_API_KEY to .env for dynamic AI generation.]

==================================================
FITBUDDY 7-DAY PERSONALIZED WORKOUT PLAN
Client: {name} | Goal: {fitness_goal} | Level: {intensity}
==================================================

DAY 1: Upper Body Strength & Hypertrophy Focus
- Warm-up (8 mins): Arm circles, shoulder dislocates with band, cat-cow stretch.
- Workout:
  * Dumbbell / Barbell Bench Press: 4 sets x 8-10 reps (Rest: 90s)
  * Bent-Over Barbell or Dumbbell Rows: 4 sets x 10 reps (Rest: 90s)
  * Overhead Dumbbell Shoulder Press: 3 sets x 10-12 reps (Rest: 60s)
  * Lat Pulldowns or Pull-ups: 3 sets x 10 reps (Rest: 60s)
  * Cable Tricep Pushdowns & Dumbbell Bicep Curls (Superset): 3 sets x 12 reps (Rest: 60s)
- Cooldown (5 mins): Chest wall stretch, cross-body shoulder stretch, child's pose.

DAY 2: Lower Body Power & Core Stability
- Warm-up (8 mins): Bodyweight squats, leg swings, glute bridges (2x15).
- Workout:
  * Goblet Squats or Barbell Back Squats: 4 sets x 8-10 reps (Rest: 120s)
  * Romanian Deadlifts (RDLs): 3 sets x 10-12 reps (Rest: 90s)
  * Walking Dumbbell Lunges: 3 sets x 12 steps per leg (Rest: 60s)
  * Standing Calf Raises: 4 sets x 15 reps (Rest: 45s)
  * Hanging Knee Raises or Planks: 3 sets x 45-second holds (Rest: 45s)
- Cooldown (5 mins): Hamstring stretch, quad stretch, pigeon pose.

DAY 3: Active Recovery & Mobility
- Activity: 30-40 minutes of brisk outdoor walking or zone 2 light cycling.
- Foam rolling: Quads, IT bands, lats, and upper back (10 mins).
- Deep mobility: Hip openers, thoracic spine rotations.

DAY 4: Push Focus & Core Hypertrophy
- Warm-up (7 mins): Incline push-ups, band pull-aparts, wrist mobility.
- Workout:
  * Incline Dumbbell Press: 4 sets x 10-12 reps (Rest: 90s)
  * Dumbbell Lateral Raises: 4 sets x 12-15 reps (Rest: 45s)
  * Bodyweight Dips or Push-ups: 3 sets to technical fatigue (Rest: 60s)
  * Overhead Tricep Extension: 3 sets x 12 reps (Rest: 60s)
  * Hanging Leg Raises / Russian Twists: 3 sets x 20 total twists (Rest: 45s)
- Cooldown (5 mins): Doorway chest stretch, overhead tricep stretch.

DAY 5: Pull Focus & Posterior Chain
- Warm-up (7 mins): Cat-cow, band pull-aparts, light face pulls.
- Workout:
  * Conventional or Trap Bar Deadlift: 3 sets x 6-8 reps (Rest: 120s)
  * Seated Cable Row (Close Grip): 4 sets x 10-12 reps (Rest: 60s)
  * Face Pulls (Rear Delts & Rotators): 4 sets x 15 reps (Rest: 45s)
  * Incline Dumbbell Bicep Curls: 3 sets x 12 reps (Rest: 60s)
  * Farmer's Carries: 3 sets x 40-meter walks (Rest: 60s)
- Cooldown (5 mins): Downward dog, lat stretches, cobra pose.

DAY 6: Full Body Conditioning & Core Circuit
- Warm-up (5 mins): Jumping jacks, hip circles, high knees.
- Workout (4 Rounds Circuit - 45s work / 15s rest):
  * Kettlebell / Dumbbell Swings
  * Mountain Climbers
  * Dumbbell Thrusters
  * Box Step-Ups or Jump Squats
  * Plank Shoulder Taps
- Cooldown (5 mins): Full body static stretching and deep diaphragmatic breathing.

DAY 7: Full Rest & Restoration
- Complete rest day. Focus on hydration, meal prep for the coming week, and 8+ hours of quality sleep.
"""


# Alias for backward compatibility
def generate_workout_plan(name: str, age: int, weight: float, fitness_goal: str, intensity: str) -> str:
    return generate_workout_gemini({
        "name": name,
        "age": age,
        "weight": weight,
        "fitness_goal": fitness_goal,
        "intensity": intensity
    })
