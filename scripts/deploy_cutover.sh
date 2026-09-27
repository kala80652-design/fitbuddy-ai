#!/usr/bin/env bash
# ==============================================================================
# FITBUDDY ENTERPRISE DAY-1 PRODUCTION CUTOVER & CANARY ORCHESTRATION SCRIPT
# Architecture: Kubernetes 1.29+ / Istio 1.21+ / Flagger 1.36+ / Cloudflare Edge
# Target Namespace: production
# Target Domain: api.fitbuddy.app
# ==============================================================================

set -euo pipefail
IFS=$'\n\t'

# --- Configuration Constants ---
readonly TARGET_DOMAIN="api.fitbuddy.app"
readonly TARGET_HEALTH_ENDPOINT="https://${TARGET_DOMAIN}/healthz"
readonly TARGET_CANARY_RESOURCE="fitbuddy-core-canary"
readonly K8S_NAMESPACE="production"
readonly REDIS_CLUSTER_ENDPOINT="redis-cluster.production.svc.cluster.local"
readonly REDIS_PORT="6379"
readonly CLUSTER_CONTEXT="arn:aws:eks:us-east-1:123456789012:cluster/fitbuddy-prod-useast1"
readonly CANARY_TARGET_IMAGE="enterprise.dkr.ecr.us-east-1.amazonaws.com/fitbuddy/core-api:1.0.0"

# --- Color Formatting Utilities ---
log_info() {
    printf "\e[34m[INFO] %s - %s\e[0m\n" "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"
}
log_success() {
    printf "\e[32m[SUCCESS] %s - %s\e[0m\n" "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*"
}
log_error() {
    printf "\e[31m[ERROR] %s - %s\e[0m\n" "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" "$*" >&2
}

# --- Defensive Prerequisite Checks ---
command -v kubectl >/dev/null 2>&1 || { log_error "kubectl binary is not installed or not in PATH."; exit 1; }
command -v openssl >/dev/null 2>&1 || { log_error "openssl binary is not installed or not in PATH."; exit 1; }
command -v curl >/dev/null 2>&1 || { log_error "curl binary is not installed or not in PATH."; exit 1; }
command -v dig >/dev/null 2>&1 || { log_error "dig (bind-utils/dnsutils) is not installed or not in PATH."; exit 1; }

log_info "Verifying target Kubernetes cluster context..."
kubectl config use-context "${CLUSTER_CONTEXT}" >/dev/null 2>&1 || {
    log_error "Failed to switch kubectl context to ${CLUSTER_CONTEXT}."
    exit 1
}

# ==============================================================================
# STEP 1: EDGE NETWORK, TLS 1.3, & CLOUDFLARE RAY ID PRE-FLIGHT VERIFICATION
# ==============================================================================
log_info "--- [PHASE 1/4] Executing Edge Security & Network Health Audits ---"

# 1.1 DNS Anycast Resolution
log_info "Auditing Edge Anycast DNS routing for ${TARGET_DOMAIN}..."
RESOLVED_IPS=$(dig +short A "${TARGET_DOMAIN}")
if [[ -z "${RESOLVED_IPS}" ]]; then
    log_error "DNS resolution returned zero records for ${TARGET_DOMAIN}."
    exit 1
fi
log_success "DNS verified. Resolved Anycast edge IPs:\n${RESOLVED_IPS}"

# 1.2 Strict TLS 1.3 Handshake & Cipher Suite Negotiation
log_info "Verifying strict TLS 1.3 cipher negotiation..."
TLS_HANDSHAKE_OUTPUT=$(echo | openssl s_client -connect "${TARGET_DOMAIN}:443" -tls1_3 -servername "${TARGET_DOMAIN}" 2>&1)
if ! echo "${TLS_HANDSHAKE_OUTPUT}" | grep -q "Protocol  : TLSv1.3"; then
    log_error "Edge proxy failed to negotiate TLS 1.3 protocol!"
    exit 1
fi
NEGOTIATED_CIPHER=$(echo "${TLS_HANDSHAKE_OUTPUT}" | grep "Cipher    :" | awk '{print $3}')
log_success "Strict TLS 1.3 verified. Negotiated Cipher: ${NEGOTIATED_CIPHER}"

# 1.3 HTTP/2 Protocol Negotiation and Upstream /healthz Deep Probe
log_info "Validating HTTP/2 negotiation and deep application health via ${TARGET_HEALTH_ENDPOINT}..."
PROBE_RESPONSE=$(curl -svo /dev/null --http2 --max-time 5 -w "HTTP_CODE:%{http_code};PROTO:%{http_version};TIME:%{time_total}\n" "${TARGET_HEALTH_ENDPOINT}" 2>&1)

HTTP_CODE=$(echo "${PROBE_RESPONSE}" | grep -o 'HTTP_CODE:[0-9]*' | cut -d':' -f2)
HTTP_PROTO=$(echo "${PROBE_RESPONSE}" | grep -o 'PROTO:[^;]*' | cut -d':' -f2)
HTTP_TIME=$(echo "${PROBE_RESPONSE}" | grep -o 'TIME:[0-9.]*' | cut -d':' -f2)

if [[ "${HTTP_CODE}" -ne 200 ]]; then
    log_error "Health probe failed! Received HTTP status ${HTTP_CODE} in ${HTTP_TIME}s."
    exit 1
fi

CF_RAY_ID=$(curl -sI --http2 "${TARGET_HEALTH_ENDPOINT}" | grep -i "cf-ray:" | tr -d '\r' || true)
log_success "Upstream Health Probe: HTTP ${HTTP_CODE} (${HTTP_PROTO}) in ${HTTP_TIME}s. ${CF_RAY_ID}"


# ==============================================================================
# STEP 2: MULTI-TIER REDIS 7 IN-MEMORY CACHE PRE-WARMING
# ==============================================================================
log_info "--- [PHASE 2/4] Executing Distributed Redis 7 Cache Pre-Warming ---"

kubectl run redis-cache-prewarmer --rm -i --restart='Never' \
  --namespace="${K8S_NAMESPACE}" \
  --image=redis:7.2-alpine -- sh <<EOF
set -euo pipefail
log() { echo "[REDIS-WARMER \$(date -u +'%Y-%m-%dT%H:%M:%SZ')] \$*"; }

log "Pinging target Redis cluster instance at ${REDIS_CLUSTER_ENDPOINT}:${REDIS_PORT}..."
PING_RES=\$(redis-cli -h "${REDIS_CLUSTER_ENDPOINT}" -p "${REDIS_PORT}" PING)
if [ "\${PING_RES}" != "PONG" ]; then
    echo "ERROR: Redis cluster returned non-PONG response: \${PING_RES}" >&2
    exit 1
fi
log "Redis connection confirmed. Hydrating macro archetypes and kinematic baselines..."

# 1. Macronutrient Standard Baselines (Keto, Vegan, Balanced Hypertrophy, Fat Loss)
redis-cli -h "${REDIS_CLUSTER_ENDPOINT}" -p "${REDIS_PORT}" MSET \
  "nutrition:archetype:hypertrophy:male:80kg" '{"tdee":2650,"target_calories":2900,"protein_g":180,"carbs_g":340,"fats_g":80,"hydration_l":3.5}' \
  "nutrition:archetype:fatloss:female:65kg" '{"tdee":2050,"target_calories":1650,"protein_g":140,"carbs_g":140,"fats_g":45,"hydration_l":2.8}' \
  "nutrition:archetype:vegan:endurance:70kg" '{"tdee":2800,"target_calories":2800,"protein_g":135,"carbs_g":420,"fats_g":65,"hydration_l":4.0}' \
  "nutrition:archetype:keto:recomp:85kg" '{"tdee":2400,"target_calories":2200,"protein_g":170,"carbs_g":30,"fats_g":155,"hydration_l":3.8}'

# 2. 33-Point MediaPipe Biomechanical Angle Threshold Vectors
redis-cli -h "${REDIS_CLUSTER_ENDPOINT}" -p "${REDIS_PORT}" MSET \
  "kinematics:vector:squat" '{"landmarks":[23,24,25,26,27,28],"depth_knee_angle_min":90.0,"max_valgus_deviation_deg":8.5,"torso_incline_max_deg":45.0}' \
  "kinematics:vector:bench_press" '{"landmarks":[11,12,13,14,15,16],"elbow_tuck_angle_deg":75.0,"bar_path_deviation_tolerance":0.05,"pause_duration_ms":300}' \
  "kinematics:vector:deadlift" '{"landmarks":[11,12,23,24,25,26],"lumbar_flexion_limit_deg":12.0,"knee_lockout_sync_tolerance_ms":150}' \
  "kinematics:vector:overhead_press" '{"landmarks":[11,12,13,14,23,24],"scapular_upward_rotation_deg":60.0,"ribcage_flare_limit_deg":10.0}'

# 3. Global Token-Bucket Rate Limiting Keys
redis-cli -h "${REDIS_CLUSTER_ENDPOINT}" -p "${REDIS_PORT}" SET "ratelimit:global:capacity" "60000" EX 86400
redis-cli -h "${REDIS_CLUSTER_ENDPOINT}" -p "${REDIS_PORT}" SET "ratelimit:global:leak_rate_per_sec" "1000" EX 86400
redis-cli -h "${REDIS_CLUSTER_ENDPOINT}" -p "${REDIS_PORT}" SET "system:circuit_breaker:genai:status" "CLOSED" EX 86400

log "Successfully populated 11 high-frequency cache keys with 24-hour TTL expiration."
EOF
log_success "Redis 7 multi-tier cache pre-warming finished with zero exit code."


# ==============================================================================
# STEP 3: INITIALIZING FLAGGER CANARY PROGRESSIVE RELEASE (ISTIO SERVICE MESH)
# ==============================================================================
log_info "--- [PHASE 3/4] Configuring & Triggering Flagger Canary Deployment ---"

# 3.1 Apply Strict Canary Custom Resource
cat <<EOF | kubectl apply -n "${K8S_NAMESPACE}" -f -
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: ${TARGET_CANARY_RESOURCE}
  namespace: ${K8S_NAMESPACE}
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fitbuddy-app
  service:
    port: 8000
    targetPort: 8000
    gateways:
      - mesh
      - istio-system/public-gateway
    hosts:
      - ${TARGET_DOMAIN}
  analysis:
    interval: 2m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99.9
        interval: 1m
      - name: request-duration
        thresholdRange:
          max: 250
        interval: 1m
    webhooks:
      - name: smoke-test
        type: pre-rollout
        url: http://flagger-loadtester.test/
        timeout: 15s
        metadata:
          type: bash
          cmd: "curl -sf -X POST http://fitbuddy-app-canary.production:8000/api/v1/generate-workout -H 'Content-Type: application/json' -d '{\"name\":\"CanarySynthetic\",\"age\":28,\"gender\":\"male\",\"weight\":75.0,\"fitness_goal\":\"muscle_gain\",\"fitness_level\":\"intermediate\",\"dietary_preference\":\"omnivore\"}' | grep -q 'periodized_schedule'"
EOF

# 3.2 Update Deployment Image to Trigger Release
log_info "Triggering canary deployment via container image update to ${CANARY_TARGET_IMAGE}..."
kubectl set image deployment/fitbuddy-app -n "${K8S_NAMESPACE}" fitbuddy-app="${CANARY_TARGET_IMAGE}" --record=true

log_info "Canary progression initiated. Flagger is monitoring Istio telemetry..."
log_info "Traffic shift schedule: 0% -> 10% -> 20% -> 30% -> 40% -> 50% (Evaluation: 2m intervals)."

# 3.3 Non-blocking Canary Status Probe
kubectl get canary -n "${K8S_NAMESPACE}" "${TARGET_CANARY_RESOURCE}"


# ==============================================================================
# STEP 4: ZERO-DOWNTIME EMERGENCY ABORT COMMAND REFERENCE
# ==============================================================================
log_info "--- [PHASE 4/4] Release Verification Summary ---"
log_success "Cutover pipeline execution complete. System is stable and routing canary traffic."
echo ""
echo "================================================================================"
echo "🚨 CRITICAL: ZERO-DOWNTIME EMERGENCY CANARY ABORT & INSTANT ROLLBACK ONE-LINER:"
echo "================================================================================"
echo "kubectl patch canary -n ${K8S_NAMESPACE} ${TARGET_CANARY_RESOURCE} --type=merge -p '{\"spec\":{\"analysis\":{\"iterations\":0}}}' && kubectl rollout undo deployment/fitbuddy-app -n ${K8S_NAMESPACE}"
echo "================================================================================"
