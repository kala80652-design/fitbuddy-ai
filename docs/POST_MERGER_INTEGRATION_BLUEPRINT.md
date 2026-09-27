# FitBuddy — Day-1 to Day-100 Post-Merger Integration (PMI) Blueprint

**Document ID:** `FITBUDDY-PMI-BLUEPRINT-2026`  
**Classification:** Corporate M&A Technical Governance & Platform Architecture  
**Author:** Transition CTO, Lead Corporate M&A Solutions Architect & Head of PMIO  
**Target Enterprise:** Global HealthTech Holdings / FitBuddy Enterprise Acquisition

---

## 1. Executive Summary & Integration Principles

This blueprint governs the comprehensive technical, structural, and operational consolidation of **FitBuddy Inc.** into the acquiring Global HealthTech enterprise over a structured 100-day execution window.

```
+========================================================================================================+
|                                100-DAY POST-MERGER TECHNICAL EXECUTION TRACK                           |
+========================================================================================================+
| PHASE 1 (Days 1–15)   : IAM, Cloudflare, AWS/GCP Root Credential & Identity Consolidation              |
| PHASE 2 (Days 16–45)  : Multi-Tenant PostgreSQL 16 Schema Isolation, Row-Level Security & Data Cutover|
| PHASE 3 (Days 46–100) : Snowflake Lakehouse ETL Integration, Centralized AI Gateway & Final SRE Handover|
+========================================================================================================+
```

---

## 2. Chronological Technical Roadmap

### 2.1 Phase 1 (Days 1–15): Infrastructure, Security, & Credential Consolidation
- **Day 1–3:** Root cloud IAM transition. Migrate AWS Root and GCP Organization credentials from founder custody to corporate `cloud-ops@acquirer.com`. Enforce mandatory Okta Enterprise SSO with FIDO2 hardware MFA.
- **Day 4–7:** Cloudflare Edge & Anycast Ingress Consolidation. Transfer DNS zone `fitbuddy.enterprise` to corporate Cloudflare enterprise tenant. Reissue mTLS certificates and re-verify Ray ID propagation across Istio 1.21 ingress gateways.
- **Day 8–15:** Secret & Encryption Key Re-wrapping. Rotate all symmetric database keys (`AES-256-GCM`), Redis cluster credentials (`FitBuddySuperSecureProdRedis2026!`), and Google Gemini API project tokens into HashiCorp Vault.

### 2.2 Phase 2 (Days 16–45): Multi-Tenant PostgreSQL 16 Schema Isolation & Tenancy Migration
- **Architecture Strategy:** FitBuddy enforces a hybrid multi-tenant isolation model utilizing PostgreSQL 16 **Row-Level Security (RLS)** with tenant discrimination keys (`tenant_id`), balancing low operational overhead with cryptographic tenant isolation.
- **Tradeoff Analysis:**
  - *Shared-Table with RLS (Adopted):* High connection pool efficiency, unified schema migrations via Alembic, sub-millisecond tenant context switching via `SET LOCAL app.current_tenant_id`.
  - *Schema-Per-Tenant (Rejected):* High migration overhead (>500 schemas), excessive catalog bloat, and connection pool starvation under high concurrent gym loads.

### 2.3 Phase 3 (Days 46–100): Snowflake Lakehouse ETL Integration & AI Gateway Centralization
- **Lakehouse Pipeline:** Ingest real-time kinematic pose angles, VBT velocity data, and HRV recovery metrics via Kafka into corporate Snowflake Medallion Lakehouse (Bronze raw ingestion $\rightarrow$ Silver sanitized $\rightarrow$ Gold actuarial analytics).
- **Centralized GenAI Gateway:** Route all FastAPI microservice LLM calls through corporate GenAI proxies with unified Redis caching, DLP prompt injection filters, and automatic Gemini 1.5 Pro $\leftrightarrow$ Flash fallback mechanics.
- **Day 100 Sign-Off:** Complete legacy SQLite sunsetting; execute final SRE operational sign-off and dissolve the Post-Merger Integration Office (PMIO).

---

## 3. Multi-Tenant PostgreSQL 16 DDL Schema & Row-Level Security (RLS)

File location: `schema/multi_tenant_rls.sql`

```sql
-- =============================================================================
-- FitBuddy Enterprise Multi-Tenant PostgreSQL 16 DDL & RLS Security Manifest
-- Guarantees cryptographic tenant isolation for B2B commercial gym chains.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Tenant Registry Table
CREATE TABLE IF NOT EXISTS enterprise_tenants (
    tenant_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_slug VARCHAR(64) UNIQUE NOT NULL,
    organization_name VARCHAR(255) NOT NULL,
    tier_plan VARCHAR(32) NOT NULL DEFAULT 'ENTERPRISE_PILOT', -- PILOT, ENTERPRISE, PRO
    allocated_seats INT NOT NULL DEFAULT 250,
    rate_limit_capacity INT NOT NULL DEFAULT 10000,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Multi-Tenant Athlete Roster Table
CREATE TABLE IF NOT EXISTS b2b_athlete_roster (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES enterprise_tenants(tenant_id) ON DELETE CASCADE,
    member_id VARCHAR(64) NOT NULL,
    trainer_id VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    age INT NOT NULL CHECK (age >= 13 AND age <= 100),
    gender VARCHAR(16) NOT NULL,
    weight_kg NUMERIC(5,2) NOT NULL,
    fitness_goal VARCHAR(32) NOT NULL,
    fitness_level VARCHAR(32) NOT NULL,
    dietary_preference VARCHAR(32) NOT NULL,
    par_q_status VARCHAR(16) NOT NULL DEFAULT 'PASSED',
    heart_rate_max INT NOT NULL,
    orthopedic_restrictions TEXT DEFAULT 'NONE',
    target_archetype VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tenant_member UNIQUE (tenant_id, member_id)
);

-- Indexing for high-throughput queries
CREATE INDEX IF NOT EXISTS idx_roster_tenant_member ON b2b_athlete_roster(tenant_id, member_id);
CREATE INDEX IF NOT EXISTS idx_roster_tenant_trainer ON b2b_athlete_roster(tenant_id, trainer_id);

-- 3. Enable Strict Row-Level Security (RLS)
ALTER TABLE b2b_athlete_roster ENABLE ROW LEVEL SECURITY;
ALTER TABLE b2b_athlete_roster FORCE ROW LEVEL SECURITY;

-- 4. Create Tenant Context Policy
DROP POLICY IF EXISTS tenant_isolation_policy ON b2b_athlete_roster;
CREATE POLICY tenant_isolation_policy ON b2b_athlete_roster
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);

-- 5. Tenant Context Session Switcher Routine
CREATE OR REPLACE FUNCTION set_tenant_context(p_tenant_id UUID) 
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant_id', p_tenant_id::text, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

## 4. Governance & Executive RACI Matrix

| Functional Workstream | Primary Deliverables & Operational Scope | Acquired Eng (FitBuddy) | Acquiring Arch | Platform SRE | Legal & Compliance | Product Lead |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Cloud IAM & Edge Cutover** | Root credential rotation, Okta SSO, Cloudflare DNSSEC, Istio 1.21 ingress gateways. | **C** | **A** | **R** | **I** | **I** |
| **Database Tenancy & RLS** | PostgreSQL 16 schema migration, RLS policies, zero-downtime data replication. | **R** | **A** | **R** | **I** | **C** |
| **GenAI Model Orchestration** | Gemini 1.5 Pro/Flash gateway integration, circuit breaker fallbacks, prompt security. | **R** | **A** | **C** | **I** | **C** |
| **Lakehouse ETL Ingestion** | Kafka streaming, Snowflake Medallion pipelines, SHA-256 biometric de-identification. | **C** | **A** | **R** | **C** | **I** |
| **Regulatory & Health Compliance** | Apple 5.1.1, Health Connect, CycloneDX 1.5 SBOM, HIPAA/GDPR validation. | **C** | **C** | **I** | **A / R** | **I** |
| **Commercial B2B Gym Rollouts** | 90-day pilot execution, trainer certification, bulk CSV ingestion pipelines. | **R** | **I** | **C** | **C** | **A** |

*Legend: **R** = Responsible for Execution; **A** = Accountable Executive; **C** = Consulted SME; **I** = Informed Stakeholder.*
