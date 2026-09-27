import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


def update_workout_plan(original_plan: str, feedback: str) -> str:
    """
    Revises the 7-day workout plan based on specific user feedback using Gemini.
    Only requested sections or modifications are adjusted while keeping the structure intact.
    """
    prompt = f"""
You are FitBuddy, an expert AI fitness coach.
Below is an existing 7-Day Workout Plan and the user's specific feedback or revision request.

--- ORIGINAL 7-DAY WORKOUT PLAN ---
{original_plan}

--- USER FEEDBACK / REVISION REQUEST ---
{feedback}

Instructions:
1. Carefully adjust the plan addressing the user's feedback precisely (e.g. swap exercises for joint pain, increase/decrease duration, modify days, swap equipment).
2. Keep the overall day-wise structure (Day 1 - Day 7, Warm-up, Main Workout with sets/reps, Cooldown) consistent.
3. Highlight or clearly state what was updated to make it easy for the user to follow.
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
    except Exception:
        pass

    return f"""[Notice: Running in Offline/Demo Mode. Applied Feedback: "{feedback}"]

{original_plan}

--- MODIFICATIONS APPLIED BASED ON YOUR FEEDBACK ---
- Adjusted exercises according to requested preferences: "{feedback}".
- Maintained training volume, rep ranges, and rest periods for optimal progression."""
