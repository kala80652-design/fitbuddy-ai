import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("fitbuddy.hardware_broker")


class RepTelemetry(BaseModel):
    device_id: str = Field(..., description="Unique serial or MAC of connected hardware")
    athlete_id: int = Field(..., description="Active athlete user ID")
    exercise_name: str = Field(..., description="Exercise being tracked (e.g., Barbell Squat, Cable Press)")
    rep_number: int = Field(..., ge=1)
    concentric_velocity_mps: float = Field(..., ge=0.0, le=5.0, description="Mean concentric velocity in m/s")
    eccentric_velocity_mps: float = Field(..., ge=0.0, le=5.0, description="Mean eccentric velocity in m/s")
    peak_power_watts: float = Field(..., ge=0.0, le=5000.0, description="Peak power output in Watts")
    rom_completion_pct: float = Field(..., ge=0.0, le=100.0, description="Range of motion completion percentage")
    timestamp: float = Field(default_factory=time.time)


class VelocityBasedTrainingEngine:
    """
    Velocity-Based Training (VBT) Fatigue & Autoregulation Engine.
    Tracks velocity loss during a working set and triggers auto-cutoff when
    fatigue exceeds defined physiological thresholds (typically 20% velocity loss).
    """

    def __init__(self, velocity_loss_threshold_pct: float = 20.0):
        self.velocity_loss_threshold_pct = velocity_loss_threshold_pct
        self.active_sets: Dict[str, list] = {}

    def process_rep(self, telemetry: RepTelemetry) -> Dict[str, Any]:
        set_key = f"{telemetry.athlete_id}_{telemetry.exercise_name}"
        
        if set_key not in self.active_sets:
            self.active_sets[set_key] = []

        set_history = self.active_sets[set_key]
        set_history.append(telemetry)

        # Baseline velocity is the first (freshest) rep of the set
        baseline_velocity = set_history[0].concentric_velocity_mps
        current_velocity = telemetry.concentric_velocity_mps

        if baseline_velocity > 0:
            velocity_loss_pct = round(((baseline_velocity - current_velocity) / baseline_velocity) * 100, 1)
        else:
            velocity_loss_pct = 0.0

        should_terminate_set = velocity_loss_pct >= self.velocity_loss_threshold_pct and len(set_history) >= 2

        response = {
            "device_id": telemetry.device_id,
            "athlete_id": telemetry.athlete_id,
            "rep_number": telemetry.rep_number,
            "current_velocity_mps": current_velocity,
            "baseline_velocity_mps": baseline_velocity,
            "velocity_loss_pct": max(0.0, velocity_loss_pct),
            "peak_power_watts": telemetry.peak_power_watts,
            "rom_completion_pct": telemetry.rom_completion_pct,
            "terminate_set_signal": should_terminate_set,
            "coaching_instruction": (
                "🚨 Terminate set: Target velocity loss exceeded (>20%). Maintain neuromuscular power."
                if should_terminate_set
                else "✅ Velocity optimal. Continue set with high concentric intent."
            )
        }

        if should_terminate_set:
            logger.info("VBT Autoregulation triggered for Athlete %d on %s (Loss: %s%%)", telemetry.athlete_id, telemetry.exercise_name, velocity_loss_pct)

        return response

    def reset_set(self, athlete_id: int, exercise_name: str) -> None:
        set_key = f"{athlete_id}_{exercise_name}"
        if set_key in self.active_sets:
            del self.active_sets[set_key]


vbt_engine = VelocityBasedTrainingEngine()
