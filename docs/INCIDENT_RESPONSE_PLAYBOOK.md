# FitBuddy – Incident Response Playbook (IRP)

**Document Classification:** RESTRICTED / SEC-OPS  
**Revision:** `2.0.0`  
**Applicability:** Production Engineering, SRE, Security Operations  

---

## 1. Incident Severity Classification Matrix

| Level | Severity | Description | Target Response Time (SLA) | Escalate To |
| :--- | :--- | :--- | :---: | :--- |
| **Sev-1** | **Critical** | Confirmed data breach, unencrypted PII/biometrics leak, active credential exposure, or total cluster outage. | $< 15\text{ minutes}$ | CISO, CTO, Lead SRE |
| **Sev-2** | **Major** | Upstream Gemini API outage, high 5xx error rate ($>5\%$), or database connection pool exhaustion. | $< 30\text{ minutes}$ | Lead SRE, Backend Lead |
| **Sev-3** | **Moderate** | Flagger canary rollback, localized rate-limiting false positives, or degraded background task latency. | $< 2\text{ hours}$ | On-Call Engineer |
| **Sev-4** | **Minor** | Non-blocking UI defect, scheduled telemetry drift, or minor documentation discrepancies. | $< 24\text{ hours}$ | Product / QA |

---

## 2. Compromised Google Gemini API Key Protocol

If a `GOOGLE_API_KEY` is leaked in public commits, logs, or third-party breaches:

```bash
# 1. Immediately revoke the compromised key in Google Cloud Console / AI Studio
# 2. Generate a new restricted API key with IP / HTTP referrer restrictions

# 3. Rotate the Secret in Kubernetes Namespace
kubectl create secret generic fitbuddy-secrets \
  --from-literal=GOOGLE_API_KEY="NEW_RESTRICTED_GEMINI_KEY" \
  --dry-run=client -o yaml | kubectl apply -f - -n fitbuddy

# 4. Trigger a zero-downtime rolling restart to evict all pods using the compromised key
kubectl rollout restart deployment/fitbuddy-web -n fitbuddy
kubectl rollout restart deployment/fitbuddy-worker -n fitbuddy

# 5. Review Cloud Console audit logs for unauthorized token spikes
```

---

## 3. Database Tampering & Breach Notification Sequence

In the event of unauthorized database access or suspected schema modification:

1. **Network Containment**:
   ```bash
   # Immediately sever ingress to PostgreSQL
   kubectl scale deployment fitbuddy-web --replicas=0 -n fitbuddy
   kubectl scale deployment fitbuddy-worker --replicas=0 -n fitbuddy
   ```
2. **Forensic Evidence Collection**:
   - Snapshot the active PostgreSQL persistent volume claims (PVCs).
   - Export WAL logs and database audit logs to an immutable S3 bucket with Object Lock enabled.
3. **Integrity Validation & Restoration**:
   - Restore database from the most recent verified encrypted snapshot prior to the breach timestamp.
4. **Regulatory Notification (GDPR Article 33 / HIPAA)**:
   - If Protected Health Information (PHI) or identifiable biometric records were exfiltrated, draft and submit notification to regulatory authorities within 72 hours.

---

## 4. Periodic Security Drills
- Run Gitleaks and Semgrep SAST on every pull request.
- Perform quarterly disaster recovery restore tests and automated Trivy container image audits.
