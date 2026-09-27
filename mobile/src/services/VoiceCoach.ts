/**
 * FitBuddy Zero-Latency On-Device Voice Coaching Service
 * Provides instant audio cues during active workouts using on-device Text-to-Speech (TTS)
 * and processes hands-free voice commands via offline Speech-to-Text (STT).
 */

import * as Speech from 'expo-speech';

export interface FormCorrectionEvent {
  exercise: string;
  reps: number;
  stage: 'up' | 'down';
  angle: number;
  criticalCue?: string;
}

class VoiceCoachService {
  private isSpeaking: boolean = false;
  private lastSpokenTime: number = 0;
  private speechCooldownMs: number = 2500; // Prevent repetitive chatter

  /**
   * Deliver an immediate, low-latency audio cue to the user.
   */
  public speakCue(text: string, priority: boolean = false): void {
    const now = Date.now();
    if (!priority && (now - this.lastSpokenTime < this.speechCooldownMs || this.isSpeaking)) {
      return;
    }

    this.lastSpokenTime = now;
    this.isSpeaking = true;

    Speech.speak(text, {
      language: 'en-US',
      pitch: 1.05,
      rate: 1.15, // Slightly faster tempo for real-time exercise execution
      onDone: () => {
        this.isSpeaking = false;
      },
      onError: () => {
        this.isSpeaking = false;
      },
    });
  }

  /**
   * Process kinematic events and trigger appropriate instant audible coaching.
   */
  public processKinematicEvent(event: FormCorrectionEvent): void {
    if (event.criticalCue) {
      this.speakCue(event.criticalCue, true);
      return;
    }

    if (event.stage === 'down' && event.angle < 95) {
      this.speakCue(`Rep ${event.reps}, good depth!`);
    } else if (event.stage === 'up' && event.angle >= 95 && event.angle < 130) {
      this.speakCue("Squat deeper on next rep");
    }
  }

  /**
   * Handle hands-free voice commands during sets.
   */
  public handleVoiceCommand(command: string): string {
    const lower = command.toLowerCase().trim();

    if (lower.includes("next set") || lower.includes("done")) {
      this.speakCue("Set logged. Starting 90 second rest timer.", true);
      return "ACTION_NEXT_SET";
    } else if (lower.includes("too heavy") || lower.includes("reduce weight")) {
      this.speakCue("Noted. Decreasing target weight by 5 percent.", true);
      return "ACTION_DECREASE_WEIGHT";
    } else if (lower.includes("pause workout")) {
      this.speakCue("Workout paused.", true);
      return "ACTION_PAUSE";
    }

    return "COMMAND_UNRECOGNIZED";
  }
}

export const voiceCoach = new VoiceCoachService();
