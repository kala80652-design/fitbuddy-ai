# FitBuddy — Intellectual Property Disclosure Schedule & Patent Claims

**Document ID:** `FITBUDDY-IP-REGISTER-2026`  
**Classification:** Proprietary / M&A Due Diligence Disclosures  
**Assignee:** FitBuddy Inc.  
**Governing Law:** United States Patent and Trademark Office (USPTO) / World Intellectual Property Organization (WIPO)

---

## 1. Formal Patentable Claims Schedule

### Claim 1: Edge-Compute Kinematic Pose Deviation Correction via Ephemeral MediaPipe Coordinate Vectors
- **Docket Number:** `PAT-FITBUDDY-001`
- **Inventors:** Lead Computer Vision Architect & Platform CTO
- **Technical Disclosure & Claim Scope:**
  1. A computer-implemented method for real-time biomechanical posture auditing during dynamic resistance training, comprising:
     - Capturing continuous optical sensor frames at $\ge 30\text{ FPS}$ on a mobile edge client device.
     - Ephemerally projecting optical frames into volatile memory to extract a 33-point skeletal landmark topological array using lightweight MediaPipe models.
     - Computing multi-planar joint angles in real time, specifically knee flexion depth ($85.0^\circ - 95.0^\circ$), lumbar overextension limits ($\le 5.0^\circ$), and concentric bar velocity ($m/s$).
     - Comparing calculated kinematic vectors against pre-warmed Redis in-memory archetype baselines (`kinematics:baseline:*`).
     - Emitting instantaneous sub-50ms corrective tactile and visual cueing without writing or transmitting raw image frames off the client device.

---

### Claim 2: Asynchronous Biomechanical Load Autoregulation Driven by Autonomic HRV and Exertion Biomarkers
- **Docket Number:** `PAT-FITBUDDY-002`
- **Inventors:** Principal Biomedical Engineer & Lead AI Architect
- **Technical Disclosure & Claim Scope:**
  1. A distributed system for dynamic physiological workout volume modulation, comprising:
     - Ingesting continuous resting heart rate, active energy expenditure, and Heart Rate Variability Root Mean Square of Successive Differences ($rMSSD$ / $SDNN$) from Apple HealthKit and Google Health Connect.
     - Calculating a composite **Autonomic Readiness Index ($0 - 100$)** based on rolling circadian deviations from a 14-day baseline.
     - Dynamically scaling planned resistance training sets, target repetitions, and Rate of Perceived Exertion (RPE) targets prior to workout execution.
     - Automatically triggering auto-deload mobility protocols when the Autonomic Readiness Index falls below a defined systemic fatigue threshold ($< 50$).

---

### Claim 3: Zero-Downtime Deterministic Fallback Circuit Breaker for Generative AI Workout Synthesizers
- **Docket Number:** `PAT-FITBUDDY-003`
- **Inventors:** Principal Site Reliability Engineer & Lead Backend Architect
- **Technical Disclosure & Claim Scope:**
  1. A fault-tolerant multi-stage orchestration system for generative exercise and sports nutrition synthesis, comprising:
     - Dispatching workout requests to an asynchronous Celery task worker pool targeting a primary foundation model (Google Gemini 1.5 Pro).
     - Monitoring inference response duration against a strict P95 threshold ($< 250\text{ms}$) and tracking upstream HTTP 429 / 5xx error rates.
     - Automatically tripping an in-memory Redis cluster circuit breaker flag (`system:circuit_breaker:genai:status`) upon threshold violation.
     - Instantly shifting execution to a sub-second Gemini 1.5 Flash secondary pipeline, and in the event of total network disconnection, engaging an offline deterministic rule matrix without failing client HTTP requests.

---

## 2. Trade Secret & Proprietary Asset Register

| Asset ID | Proprietary Asset Title | Technical Description & Protection Mechanisms |
| :--- | :--- | :--- |
| **TS-001** | **Multi-Factor Macro Rebalancing Algorithm** | Proprietary algorithm calculating adaptive intra-workout macronutrient re-allocations based on real-time wearable caloric burn rates and glycemic load targets. Encrypted in core backend bytecode. |
| **TS-002** | **33-Point MediaPipe Spatial Smoothing Filter** | Dynamic exponential moving average (EMA) jitter filter tailored for barbell barbell path tracking under variable gym lighting conditions. |
| **TS-003** | **Prompt Topology & Few-Shot Orthopedic Embeddings** | Curated clinical prompt structures containing physical therapy contraindication mappings preventing biomechanical injury during automated plan generation. |
| **TS-004** | **Hardware Broker MQTT Compression Protocol** | High-throughput serialization schema streaming sub-10ms velocity transducer telemetry into the FastAPI asyncio ingestion broker. |

---

## 3. Clean-Room Open-Source Software (OSS) Attestation

1. **Zero Copyleft Contamination:** A full automated source code audit confirms that **0.0%** of backend, frontend, worker, or mobile repositories contain code licensed under GNU GPLv1/v2/v3, GNU AGPL, SSPL, or EUPL.
2. **Permissive Licensing Profile:** 100% of third-party libraries adhere strictly to permissive licenses (**MIT**, **Apache-2.0**, and **BSD-3-Clause**), guaranteeing clear title and unencumbered commercial ownership for acquiring entities.
3. **Third-Party Patent Retaliation Immunity:** All component licenses protect against patent assertion and grant broad royalty-free execution rights.
