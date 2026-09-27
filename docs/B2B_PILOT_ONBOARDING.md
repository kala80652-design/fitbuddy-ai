# FitBuddy — B2B Enterprise Gym & Trainer Pilot Onboarding Playbook

**Document ID:** `FITBUDDY-B2B-PILOT-2026`  
**Classification:** Enterprise Operations & Commercial GTM  
**Target Audience:** Gym Owners, Fitness Directors, Head Coaches, and Personal Trainers  
**Platform Release:** FitBuddy Enterprise v2.4.0 (Cloud-Native Kubernetes 1.29+ / Istio 1.21+)

---

## 1. Executive & Commercial Framework

The **FitBuddy B2B Enterprise Pilot** equips commercial gym chains, boutique fitness studios, and personal training facilities with an enterprise-grade, AI-augmented biomechanical co-pilot and sports nutrition engine.

```
+========================================================================================================+
|                                    90-DAY ENTERPRISE PILOT LIFECYCLE                                   |
+========================================================================================================+
| [Days 1 - 7]   : Facility Provisioning, SSO Integration, & Trainer Certification (15-Min Quickstart)  |
| [Days 8 - 30]  : Bulk Client Ingestion, Baseline Biometric Profiling & Initial Plan Synthesis          |
| [Days 31 - 60] : Active Training Workflows, HITL Form Auditing & Autonomic Recovery Auto-Deloading     |
| [Days 61 - 90] : Mid-Pilot Review, SLA Verification Audit, and Commercial Transition to Scale          |
+========================================================================================================+
```

### 1.1 Commercial Terms & Per-Seat Billing Mechanics
- **Pilot Duration:** 90 Calendar Days from tenant provisioning date.
- **Seat Allocation:** Up to 15 Certified Personal Trainers and 250 Active Client Profiles per facility during the pilot window.
- **Commercial Rate:** $2.50 / active athlete seat / month post-pilot conversion (billed monthly in arrears based on peak high-water mark active seats).
- **Enterprise Volume Discounts:**
  - 251 – 1,000 seats: $2.15 / seat / month.
  - 1,001 – 5,000 seats: $1.85 / seat / month.
  - 5,001+ seats: Custom Enterprise Contract with dedicated single-tenant VPC peering.
- **Data Sovereignty:** The commercial partner retains 100% exclusive proprietary ownership of athlete and trainer records. FitBuddy legally warrants that athlete telemetry is never ingested into public foundation model training corpora.

### 1.2 Enterprise Service Level Commitments (SLA)
| Metric | Service Target | Remediation & Financial Credit |
| :--- | :--- | :--- |
| **API Availability** | **99.9% Monthly Uptime** | 10% monthly service credit for each 0.1% degradation below target. |
| **P95 Plan Latency** | **< 250ms** for cached/Flash plans; **< 2.5s** for full periodized Gemini 1.5 Pro synthesis | Automatic seamless failover to Gemini 1.5 Flash in-memory circuit breaker. |
| **Edge Vision Inference** | **≥ 30 FPS** on iOS (A13 Bionic+) and Android (Snapdragon 778G+) | Client-side graceful fallback to deterministic cadence timer. |
| **Incident MTTA / MTTR** | **< 2 min MTTA / < 15 min MTTR** for Sev-1; **< 10 min MTTA / < 45 min MTTR** for Sev-2 | 24/7 dedicated SRE bridge and PagerDuty escalations. |

---

## 2. Trainer Onboarding & Human-in-the-Loop (HITL) Overrides

### 2.1 15-Minute Trainer Certification Workflow
```
+--------------------------------------------------------------------------------------------------------+
|                                    15-MINUTE TRAINER CERTIFICATION                                     |
+--------------------------------------------------------------------------------------------------------+
| [00:00 - 03:00] : Step 1 - Log in to Coach Command Center (/templates/coach_dashboard.html)           |
| [03:00 - 07:00] : Step 2 - Bulk Ingest Client Roster via RFC 4180 CSV Validation Pipeline             |
| [07:00 - 11:00] : Step 3 - Review Autonomic Recovery Scores & Execute 1-Click HITL Workout Overrides  |
| [11:00 - 15:00] : Step 4 - Audit Edge 33-Point MediaPipe Pose Tracking in the Weight Room             |
+--------------------------------------------------------------------------------------------------------+
```

### 2.2 Human-in-the-Loop (HITL) Override & Physical Therapy Contraindication Policy
Trainers retain complete, overriding authority over all AI-generated routines. When an athlete presents acute musculoskeletal injuries or physical therapy contraindications:
1. **Contraindication Tagging:** The trainer selects orthopedic restriction tags (e.g., `LUMBAR_DISC_HERNIATION_L4_L5`, `PATELLAR_TENDINOPATHY`, `SHOULDER_IMPINGEMENT_SUBACROMIAL`).
2. **Instant Biomechanical Pruning:** The backend generator automatically excises prohibited kinematic planes (e.g., eliminates spinal axial loading > 0.5x bodyweight or deep knee flexion > 90°).
3. **Trainer Natural Language Modification:** The trainer inputs plain text coaching instructions (e.g., *"Replace Barbell Back Squat with Belt Squat and elevate heels on 15° wedge"*).
4. **1-Click Sync:** Clicking **"Approve & Sync to Athlete App"** immediately broadcasts the verified routine across the client's mobile app and Apple Watch via authenticated WebSockets.

---

## 3. Bulk Client Ingestion Pipeline

### 3.1 RFC 4180 Compliant CSV Schema
Commercial partners can ingest hundreds of client profiles in a single bulk operation. The CSV file must adhere strictly to the following header specification:

```csv
member_id,trainer_id,name,age,gender,weight_kg,fitness_goal,fitness_level,dietary_preference,par_q_status,heart_rate_max,orthopedic_restrictions,target_archetype
MBR-1001,TRN-042,Marcus Vance,30,male,82.5,muscle_gain,advanced,omnivore,PASSED,190,NONE,hypertrophy_male_80kg
MBR-1002,TRN-042,Elena Rostova,27,female,62.0,fat_loss,intermediate,vegan,PASSED,185,PATELLAR_SENSITIVITY,fat_loss_female_65kg
MBR-1003,TRN-088,David Chen,45,male,91.0,general_fitness,beginner,keto,PASSED,175,LUMBAR_TIGHTNESS,keto_bodybuilding_85kg
MBR-1004,TRN-088,Sophia Al-Mansoor,34,female,58.5,endurance,advanced,omnivore,PASSED,192,NONE,endurance_runner_70kg
MBR-1005,TRN-104,James Wilson,62,male,78.0,mobility_health,beginner,omnivore,PASSED,160,ROTATOR_CUFF_IMPINGEMENT,senior_mobility_60kg
```

### 3.2 Asynchronous Python / Pandas Verification & PostgreSQL 16 Ingestion Script
File location: `scripts/ingest_b2b_roster.py`

```python
#!/usr/bin/env python3
"""
FitBuddy Enterprise B2B Client Roster Bulk Ingestion Engine
Validates RFC 4180 CSV files using Pandas, applies strict schema checks,
and performs asynchronous batch inserts into PostgreSQL 16.
"""

import asyncio
import os
import sys
import uuid
from typing import List, Dict, Any
import pandas as pd
import asyncpg

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://fitbuddy_admin:FitBuddyProdPostgresSecurePassword2026!@127.0.0.1:5432/fitbuddy_enterprise_db"
)

REQUIRED_COLUMNS = [
    "member_id", "trainer_id", "name", "age", "gender", 
    "weight_kg", "fitness_goal", "fitness_level", "dietary_preference", 
    "par_q_status", "heart_rate_max", "orthopedic_restrictions", "target_archetype"
]

VALID_GOALS = {"muscle_gain", "fat_loss", "endurance", "general_fitness", "mobility_health"}
VALID_LEVELS = {"beginner", "intermediate", "advanced", "elite"}
VALID_DIETS = {"omnivore", "vegetarian", "vegan", "keto", "paleo", "pescatarian"}

def validate_roster_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validates dataframe schema, data types, and business constraints."""
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"CSV missing mandatory columns: {missing_cols}")
    
    # Clean string fields
    for col in ["member_id", "trainer_id", "name", "gender", "fitness_goal", "fitness_level", "dietary_preference", "par_q_status", "orthopedic_restrictions", "target_archetype"]:
        df[col] = df[col].astype(str).str.strip()
    
    # Cast numerical columns
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["weight_kg"] = pd.to_numeric(df["weight_kg"], errors="coerce")
    df["heart_rate_max"] = pd.to_numeric(df["heart_rate_max"], errors="coerce")
    
    if df[["age", "weight_kg", "heart_rate_max"]].isnull().any().any():
        raise ValueError("Non-numeric or null values found in age, weight_kg, or heart_rate_max.")
    
    # Value domain constraints
    if not df["fitness_goal"].isin(VALID_GOALS).all():
        invalid = df[~df["fitness_goal"].isin(VALID_GOALS)]["fitness_goal"].unique()
        raise ValueError(f"Invalid fitness goals detected: {invalid}")
        
    if not df["fitness_level"].isin(VALID_LEVELS).all():
        invalid = df[~df["fitness_level"].isin(VALID_LEVELS)]["fitness_level"].unique()
        raise ValueError(f"Invalid fitness levels detected: {invalid}")

    return df

async def stream_to_postgres(df: pd.DataFrame, tenant_id: str):
    """Streams validated records into PostgreSQL 16 using batch COPY / transaction."""
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        async with conn.transaction():
            print(f"[INGEST] Processing {len(df)} records for tenant: {tenant_id}...")
            
            records_to_insert = []
            for _, row in df.iterrows():
                records_to_insert.append((
                    str(uuid.uuid4()),
                    tenant_id,
                    row["member_id"],
                    row["trainer_id"],
                    row["name"],
                    int(row["age"]),
                    row["gender"].lower(),
                    float(row["weight_kg"]),
                    row["fitness_goal"].lower(),
                    row["fitness_level"].lower(),
                    row["dietary_preference"].lower(),
                    row["par_q_status"].upper(),
                    int(row["heart_rate_max"]),
                    row["orthopedic_restrictions"],
                    row["target_archetype"]
                ))
            
            # Execute batch insertion
            query = """
                INSERT INTO b2b_athlete_roster (
                    id, tenant_id, member_id, trainer_id, name, age, gender,
                    weight_kg, fitness_goal, fitness_level, dietary_preference,
                    par_q_status, heart_rate_max, orthopedic_restrictions, target_archetype
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                ON CONFLICT (tenant_id, member_id) DO UPDATE SET
                    weight_kg = EXCLUDED.weight_kg,
                    fitness_goal = EXCLUDED.fitness_goal,
                    fitness_level = EXCLUDED.fitness_level,
                    orthopedic_restrictions = EXCLUDED.orthopedic_restrictions,
                    updated_at = NOW();
            """
            await conn.executemany(query, records_to_insert)
            print(f"[SUCCESS] Successfully ingested {len(records_to_insert)} athletes into PostgreSQL 16.")
    finally:
        await conn.close()

def main():
    if len(sys.argv) < 3:
        print("Usage: python ingest_b2b_roster.py <path_to_csv> <tenant_id>")
        sys.exit(1)
        
    csv_path = sys.argv[1]
    tenant_id = sys.argv[2]
    
    print(f"[START] Reading and validating CSV: {csv_path}")
    df_raw = pd.read_csv(csv_path)
    df_validated = validate_roster_dataframe(df_raw)
    
    asyncio.run(stream_to_postgres(df_validated, tenant_id))

if __name__ == "__main__":
    main()
```
