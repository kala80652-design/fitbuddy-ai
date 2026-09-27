# FitBuddy — Partner Certification & Hardware Integration Guide

**Document ID:** `FITBUDDY-PARTNER-SPEC-2026`  
**Target:** Third-Party Connected Gym Hardware Manufacturers, Smart Wearables, & Corporate Wellness Brokers  
**Classification:** Open Biomechanics Ecosystem Specification  

---

## 1. "Works with FitBuddy" Certification Framework

Hardware vendors producing smart barbells, sensor-instrumented cable stations, motorized resistance racks, or smart wearables can earn official **"Works with FitBuddy"** compliance certification by adhering to the following protocols.

```
+------------------------------------------------------------------------------------+
|                         HARDWARE INTEGRATION PIPELINE                              |
+------------------------------------------------------------------------------------+
| [Smart Hardware] -> MQTT / WebSocket -> [app/hardware_broker.py] -> [VBT Engine]   |
|                                                                                    |
| Concentric Vel (m/s) | Peak Power (W) | ROM (%) -> Auto-Cutoff Signal (>20% loss)  |
+------------------------------------------------------------------------------------+
```

### 1.1 Technical Telemetry Requirements
1. **Sampling Frequency:** Minimum $\ge 50\text{ Hz}$ for continuous velocity/load transducer streams; $\ge 30\text{ FPS}$ for optical sensor arrays.
2. **Standard Payload Schema:** Ingested via WebSocket or MQTT into [`app/hardware_broker.py`](file:///c:/Users/Admin/Desktop/TN%20SKILL%20PRO/app/hardware_broker.py):
   ```json
   {
     "device_id": "BARBELL-SMART-9921",
     "athlete_id": 482,
     "exercise_name": "Barbell Squat",
     "rep_number": 3,
     "concentric_velocity_mps": 0.68,
     "eccentric_velocity_mps": 0.45,
     "peak_power_watts": 820.0,
     "rom_completion_pct": 98.5,
     "timestamp": 1774782910.2
   }
   ```
3. **Low-Latency Feedback:** VBT fatigue cut-off signals must round-trip in $< 80\text{ ms}$ over local Wi-Fi / BLE 5.3 mesh.

---

## 2. Enterprise Single Sign-On (SSO) & SCIM Directory Synchronization

### 2.1 Supported Identity Providers (IdP)
- **Okta** (SAML 2.0 & SCIM 2.0)
- **Microsoft Entra ID / Azure Active Directory** (SAML 2.0 & SCIM 2.0)
- **Google Workspace Enterprise** (SAML 2.0)

### 2.2 SCIM v2.0 Ingestion Endpoints
FitBuddy supports standard SCIM endpoints for automated HR onboarding/offboarding:
- `POST /scim/v2/Users`: Provision new employee profile into corporate wellness pool.
- `PATCH /scim/v2/Users/{id}`: Update department, employment status, or role.
- `DELETE /scim/v2/Users/{id}`: Soft-delete athlete profile; archive compliance records under $k$-anonymity guarantees.

---

## 3. Privacy & Actuarial Governance: Strict $k$-Anonymity ($k \ge 25$)

To protect individual employee privacy while supplying HR directors with data for corporate wellness healthcare premium credits:
- **Query Masking:** Queries targeting cohorts with fewer than $25$ employees return an HTTP `403 Forbidden` with error code `INSUFFICIENT_COHORT_K_ANONYMITY`.
- **Zero Raw Metric Exposure:** Individual weights, body compositions, and daily session times are strictly inaccessible through corporate administrative tokens.
- **Reporting Metrics:** Only aggregated deltas (e.g., *Cohort Avg RHR Delta: -4.2 BPM*, *Total Aerobic Compliance: 84%*) are rendered in [`templates/corporate_dashboard.html`](file:///c:/Users/Admin/Desktop/TN%20SKILL%20PRO/templates/corporate_dashboard.html).
