"""
FitBuddy Adaptive Daily Coach & Biometric IoT Modulator
Ingests wearable health metrics (Apple HealthKit / Google Health Connect)
and dynamically modulates daily training volume & intensity based on Recovery Scores.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field

class WearableTelemetryInput(BaseModel):
    user_id: str
    resting_heart_rate: float = Field(..., ge=30, le=150, description="Resting Heart Rate (bpm)")
    hrv_sdnn: float = Field(..., ge=10, le=250, description="Heart Rate Variability SDNN (ms)")
    sleep_duration_hours: float = Field(..., ge=0, le=24)
    deep_sleep_percent: float = Field(..., ge=0, le=100)
    baseline_hrv: float = Field(default=55.0, description="30-day Rolling Average HRV (ms)")

def calculate_recovery_score(telemetry: WearableTelemetryInput) -> Dict[str, Any]:
    """
    Computes CNS & Autonomic Recovery Score (0-100) using HRV deviation and sleep metrics.
    """
    hrv_deviation = ((telemetry.hrv_sdnn - telemetry.baseline_hrv) / telemetry.baseline_hrv) * 100.0
    
    # Base recovery calculation
    recovery_score = 70.0 + (hrv_deviation * 0.5)
    
    # Sleep duration adjustment
    if telemetry.sleep_duration_hours < 6.0:
        recovery_score -= 15.0
    elif telemetry.sleep_duration_hours >= 7.5:
        recovery_score += 10.0
        
    # Deep sleep quality adjustment
    if telemetry.deep_sleep_percent >= 20.0:
        recovery_score += 5.0
    elif telemetry.deep_sleep_percent < 10.0:
        recovery_score -= 10.0

    # Clamp recovery score between 0 and 100
    recovery_score = max(10.0, min(100.0, round(recovery_score, 1)))

    # Determine Prescription & Intensity Modulation
    if recovery_score < 45.0:
        status = "RED_FLAG_FATIGUE"
        prescription = "High autonomic fatigue detected. Scale back training volume by 40% or substitute an active recovery mobility routine."
        intensity_factor = 0.60
    elif recovery_score < 70.0:
        status = "MODERATE_RECOVERY"
        prescription = "Moderate recovery state. Execute planned workout with a 10% reduction in working set weights."
        intensity_factor = 0.90
    else:
        status = "PRIME_RECOVERY"
        prescription = "Optimal physiological readiness! You are fully recovered to push maximum intensity and progressive overload."
        intensity_factor = 1.05

    return {
        "user_id": telemetry.user_id,
        "recovery_score": recovery_score,
        "status": status,
        "intensity_factor": intensity_factor,
        "coaching_prescription": prescription,
    }
