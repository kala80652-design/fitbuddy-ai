# FitBuddy – Day-1 Launch Control, War-Room Runbook & Commercial Operations Pack

**Document Classification:** RESTRICTED / GTM-OPERATIONS  
**Target Systems:** Kubernetes (EKS/GKE), Cloudflare Edge, Redis 7 Cluster, PostgreSQL 16, Stripe API, App Store & Google Play  
**Execution Lead:** Principal Platform Architect, Lead SRE, VP of Growth  

---

## 1. Launch Control & War-Room Runbook

### 1.1 Pre-Flight CLI-Ready Execution Sequence

```bash
#!/usr/bin/env bash
set -eo pipefail

echo "=========================================================="
echo " [WAR-ROOM] Initiating FitBuddy Day-1 Launch Sequence"
echo "=========================================================="

# 1. Cloudflare DNS & Edge SSL Cutover Verification
echo ">>> [1/4] Verifying Cloudflare Edge & Strict TLS 1.3 Termination..."
curl -sI https://api.fitbuddy.com/healthz | grep -E "HTTP/|cf-ray|strict-transport-security"

# 2. Redis 7 Cache Pre-Warming (Top Nutrition Queries & Kinematic Baselines)
echo ">>> [2/4] Pre-Warming Redis 7 In-Memory Cache..."
python3 - << 'EOF'
import redis, os, json

r = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# Pre-load common macro splits to eliminate initial cold LLM calls
common_goals = ["muscle_hypertrophy", "fat_loss", "strength_power", "endurance"]
for goal in common_goals:
    key = f"cache:nutrition:default:{goal}"
    data = {
        "calories": 2400 if "muscle" in goal else 1900,
        "protein_g": 180,
        "carbs_g": 220,
        "fat_g": 65,
        "hydration_liters": 3.5,
        "status": "CACHED_PREWARM"
    }
    r.set(key, json.dumps(data), ex=86400)

print(" Redis pre-warm complete: Top macro vectors loaded into memory.")
EOF

# 3. Flagger Canary Release Deployment
echo ">>> [3/4] Triggering Flagger Progressive Canary Rollout..."
kubectl set image deployment/fitbuddy-web web=fitbuddy:1.0.0-prod -n fitbuddy

# 4. Monitor Canary Progression
echo ">>> [4/4] Monitoring Canary Step Weight & Metric Gates..."
kubectl get canary fitbuddy-web-canary -n fitbuddy -w
```

### 1.2 Incident Escalation Matrix & Emergency Rollbacks

| Severity | SLA | Trigger Threshold | Primary Owner | Automated / CLI Remediation Command |
| :---: | :---: | :--- | :--- | :--- |
| **Sev-1** | **< 5 min** | Global HTTP 5xx > 1% OR total mobile sync failure | Lead SRE / Architect | `kubectl -n fitbuddy annotate canary/fitbuddy-web-canary flagger.app/status="failed"` (Instant rollback to stable version) |
| **Sev-2** | **< 15 min** | Gemini API 429 Quota Exhaustion OR P95 Latency > 3000ms | AI Lead / Backend SRE | `kubectl -n fitbuddy set env deployment/fitbuddy-web FORCE_MODEL_FALLBACK="gemini-1.5-flash"` |
| **Sev-3** | **< 1 hour** | Celery queue backlog > 150 tasks | Backend SRE | `kubectl -n fitbuddy scale deployment/fitbuddy-worker --replicas=8` |

---

## 2. Store Approval, Community & Organic GTM

### 2.1 App Store & Google Play Review Board Declarations

#### Apple HealthKit Review Declaration (Guideline 5.1.1)
```text
FitBuddy utilizes Apple HealthKit strictly to read HKQuantityTypeIdentifierHeartRate,
HKQuantityTypeIdentifierActiveEnergyBurned, and HKQuantityTypeIdentifierHeartRateVariabilitySDNN.
These metrics are processed client-side and stored with AES-256 field-level encryption exclusively
to compute the user's daily central nervous system (CNS) recovery score and dynamically modulate
workout intensity. Biometric telemetry is never transmitted to third parties, used for advertising,
or repurposed.
```

#### Google Play Health Connect Permission Declaration
```text
Permissions for Resting Heart Rate and Sleep Architecture are requested strictly to power
FitBuddy's physiological workout periodization engine. Users maintain granular opt-in/opt-out
control in settings, and data retention adheres to GDPR/HIPAA-ready zero-trust policies.
```

### 2.2 App Store Optimization (ASO) Metadata

- **Title (30 chars):** `FitBuddy: AI Workout Coach`
- **Subtitle (30 chars):** `Real-Time Vision & Form Coach`
- **Keyword Set (100 chars):** `ai fitness,workout tracker,form coach,squat counter,hrv recovery,calisthenics,rep counter,gym log`
- **Short Description (80 chars):** `Real-time AI form correction, on-device pose tracking, and adaptive HRV workout plans.`

---

## 3. B2B Enterprise Gym Pilot Onboarding Kit

### 3.1 90-Day Pilot Agreement & SLA Terms

1. **Service Level Agreement (SLA):** 99.9% uptime commitment on API ingestion and [Coach Command Center](file:///c:/Users/Admin/Desktop/TN%20SKILL%20PRO/templates/coach_dashboard.html) availability.
2. **Data Residency & Security:** All athlete biometric data is encrypted at rest (AES-256) and segregated by PostgreSQL Row-Level Security (RLS) per gym tenant.
3. **Human-in-the-Loop (HITL) Authority:** Personal trainers hold absolute override control to modify, lock, or replace any AI-generated exercise or macronutrient recommendation prior to athlete execution.

### 3.2 15-Minute Personal Trainer Quickstart Guide

1. **Log in to Coach Portal:** Access `https://fitbuddy.com/coach` with your organization credentials.
2. **Roster Bulk Ingestion:** Upload athlete rosters via standard CSV (`name, email, age, weight_kg, primary_goal, injury_notes`).
3. **Inspect Biometric Recovery:** Review the morning dashboard to observe automated HRV Readiness:
   - 🟢 **Prime Recovery (Score 70-100):** Prescribe scheduled high-intensity/progressive overload workouts.
   - 🟡 **Moderate Recovery (Score 45-69):** 10% volume reduction applied automatically.
   - 🔴 **High Fatigue (Score < 45):** Active recovery or mobility substitution suggested.
4. **Override / Approve Routine:** Click *"Apply HITL Override"* to fine-tune sets, reps, or exercise selections with real-time sync to the athlete's mobile device.

---

## 4. Production Telemetry, Revenue & Health SQL Queries

Execute these index-optimized queries against your PostgreSQL 16 database to monitor launch performance:

```sql
-- ============================================================================
-- 1. Daily Active Users (DAU) & Workout Completion Velocity
-- ============================================================================
SELECT 
    DATE_TRUNC('day', wp.created_at) AS report_date,
    COUNT(DISTINCT wp.user_id) AS active_workout_users,
    COUNT(wp.id) AS total_plans_generated,
    COUNT(wp.updated_plan) AS revised_plans_count,
    ROUND(COUNT(wp.updated_plan)::numeric / NULLIF(COUNT(wp.id), 0) * 100, 2) AS revision_rate_pct
FROM workout_plans wp
WHERE wp.created_at >= NOW() - INTERVAL '7 DAYS'
GROUP BY 1
ORDER BY 1 DESC;

-- ============================================================================
-- 2. Kinematic & AI Generation Latency Percentiles
-- ============================================================================
SELECT 
    'api_workout_generation' AS pipeline_stage,
    ROUND(AVG(latency_ms), 2) AS avg_latency_ms,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY latency_ms)::numeric, 2) AS p50_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)::numeric, 2) AS p95_ms,
    ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY latency_ms)::numeric, 2) AS p99_ms
FROM (
    SELECT CAST(REGEXP_REPLACE(original_plan, '^.*latency_ms":([0-9.]+).*$', '\1') AS NUMERIC) AS latency_ms
    FROM workout_plans
    WHERE created_at >= NOW() - INTERVAL '24 HOURS'
) sub
WHERE latency_ms IS NOT NULL;

-- ============================================================================
-- 3. Stripe ARR & Free-to-Pro Conversion Velocity
-- ============================================================================
SELECT 
    tier,
    COUNT(user_id) AS total_subscribers,
    SUM(mrr_contribution) AS total_mrr_usd,
    SUM(mrr_contribution) * 12 AS total_arr_usd
FROM (
    SELECT 
        user_id,
        CASE 
            WHEN intensity = 'B2B_SEAT' THEN 'B2B Gym Seat ($2.50/seat)'
            WHEN fitness_goal = 'PRO_TIER' THEN 'FitBuddy Pro ($14.99/mo)'
            ELSE 'Free Tier ($0.00)'
        END AS tier,
        CASE 
            WHEN intensity = 'B2B_SEAT' THEN 2.50
            WHEN fitness_goal = 'PRO_TIER' THEN 14.99
            ELSE 0.00
        END AS mrr_contribution
    FROM users
) users_billing
GROUP BY tier
ORDER BY total_arr_usd DESC;
```
