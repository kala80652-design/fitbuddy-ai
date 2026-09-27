import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)


def generate_nutrition_tip_with_flash(goal: str, intensity: str = "Moderate", weight: float = 70.0) -> str:
    """
    Generates concise, practical nutrition or recovery tips aligned to the user's fitness goal using Gemini Flash.
    """
    prompt = f"""
You are a certified sports nutritionist.
Provide a concise, practical, and highly impactful Nutrition & Recovery Guide for an individual with:
- Primary Fitness Goal: {goal}
- Training Intensity: {intensity}
- Body Weight: {weight} kg

Include:
1. Daily Calorie & Macronutrient guidance (Protein, Carbs, Healthy Fats focus in grams or ratios).
2. Pre-workout & Post-workout meal/snack ideas.
3. Hydration strategy and sleep/recovery recommendation.

Keep it concise, bulleted, actionable, and direct.
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
    except Exception:
        pass

    return f"""- Daily Calories & Macros: Target ~2.0g protein per kg bodyweight ({round(weight * 2.0)}g/day) to support muscle recovery. Prioritize complex carbs (oats, brown rice, sweet potatoes) around workout windows.
- Pre-Workout: Consume 25-35g carbs + 15g protein 45-60 minutes prior (e.g. banana with whey protein or oatmeal with peanut butter).
- Post-Workout: Rehydrate and take 30g fast-digesting protein + 40g carbs within 90 minutes.
- Hydration & Recovery: Drink at least 3 to 3.5 liters of clean water daily. Target 7.5 to 8.5 hours of uninterrupted sleep for neuromuscular repair."""


# Alias for backward compatibility
def generate_nutrition_tip(fitness_goal: str, intensity: str = "Moderate", weight: float = 70.0) -> str:
    return generate_nutrition_tip_with_flash(goal=fitness_goal, intensity=intensity, weight=weight)
