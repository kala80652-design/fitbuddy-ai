#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# FITBUDDY ENTERPRISE DAY-1 CANARY CUTOVER & VERIFICATION RUNBOOK
# Target: Production Kubernetes Ingress & Edge Proxy
# ==============================================================================

DOMAIN="api.fitbuddy.app"
HEALTH_URL="https://${DOMAIN}/healthz"
CANARY_NAME="fitbuddy-core-canary"
NAMESPACE="production"
REDIS_HOST="redis-cluster.production.svc.cluster.local"
REDIS_PORT="6379"

echo "=== [STEP 1/4] EXECUTING EDGE NETWORK & TLS 1.3 VALIDATION ==="

# 1. DNS Resolution Check
echo "Auditing Cloudflare Edge DNS resolution..."
RESOLVED_IPS=$(dig +short ${DOMAIN})
if [ -z "${RESOLVED_IPS}" ]; then
  echo "[-] ERROR: DNS resolution failed for ${DOMAIN}" >&2
  exit 1
fi
echo "[+] DNS Resolved successfully: ${RESOLVED_IPS}"

# 2. TLS 1.3 Handshake Verification
echo "Verifying strict TLS 1.3 handshake and cipher suite..."
TLS_CHECK=$(openssl s_client -connect ${DOMAIN}:443 -tls1_3 -servername ${DOMAIN} < /dev/null 2>&1 | grep "Protocol" || true)
if [[ "${TLS_CHECK}" != *"TLSv1.3"* ]]; then
  echo "[-] ERROR: Strict TLS 1.3 handshake failed!" >&2
  exit 1
fi
echo "[+] TLS 1.3 Connection Verified: ${TLS_CHECK}"

# 3. Upstream Deep Health Check
echo "Querying /healthz probe endpoint..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${HEALTH_URL}")
if [ "${HTTP_STATUS}" -ne 200 ]; then
  echo "[-] ERROR: Health probe returned HTTP ${HTTP_STATUS}" >&2
  exit 1
fi
echo "[+] Health probe healthy (HTTP 200 OK)."


echo "=== [STEP 2/4] PRE-WARMING REDIS 7 CLUSTER CACHE ==="

kubectl run redis-prewarmer --rm -i --restart='Never' --namespace="${NAMESPACE}" \
  --image=redis:7-alpine -- sh <<EOF
set -e
echo "Hydrating high-frequency nutrition embeddings and exercise kinematics..."

# Hydrate top-50 exercise kinematic angle baselines (e.g. Squats, Bench Press, Romanian Deadlift)
redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} SET "kinematics:exercise:squat:knee_flexion_min" "90" EX 86400
redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} SET "kinematics:exercise:bench_press:elbow_flair_max" "75" EX 86400
redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} SET "kinematics:exercise:deadlift:spine_deviation_max" "15" EX 86400

# Seed common metabolic and TDEE profile tokens
redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} SET "nutrition:baseline:male:hypertrophy:2500" '{"target_daily_calories":2500,"protein_grams":180,"carbs_grams":260,"fats_grams":75}' EX 86400
redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} SET "nutrition:baseline:female:fat_loss:1800" '{"target_daily_calories":1800,"protein_grams":135,"carbs_grams":160,"fats_grams":50}' EX 86400

# Initialize global rate-limiting token buckets
redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} SET "ratelimit:global:burst_capacity" "10000" EX 3600
echo "[+] Redis 7 cache pre-warming completed successfully."
EOF


echo "=== [STEP 3/4] INITIALIZING FLAGGER CANARY PROGRESSIVE RELEASE ==="

# Apply Canary Resource Configuration
cat <<EOF | kubectl apply -n "${NAMESPACE}" -f -
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: ${CANARY_NAME}
  namespace: ${NAMESPACE}
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
          cmd: "curl -sd '{\"name\":\"CanaryProbe\",\"age\":25,\"gender\":\"male\",\"weight\":75.0,\"fitness_goal\":\"muscle_gain\",\"fitness_level\":\"intermediate\",\"dietary_preference\":\"omnivore\"}' -H 'Content-Type: application/json' http://fitbuddy-app-canary.production:8000/api/v1/generate-workout | grep -q 'periodized_schedule'"
EOF

echo "Triggering canary deployment by updating deployment image tag..."
kubectl set image deployment/fitbuddy-app -n "${NAMESPACE}" fitbuddy-app=enterprise.dkr.ecr.us-east-1.amazonaws.com/fitbuddy/core-api:1.0.0

echo "Watching Canary rollout progression (Target weight increments: 10% per 2m up to 50%)..."
kubectl get canary -n "${NAMESPACE}" ${CANARY_NAME} -w &
CANARY_PID=$!
sleep 15
kill ${CANARY_PID} 2>/dev/null || true


echo "=== [STEP 4/4] EMERGENCY ABORT COMMAND ONE-LINER (REFERENCE) ==="
echo "To instantly halt rollout and roll back to stable pods, execute:"
echo "kubectl patch canary -n ${NAMESPACE} ${CANARY_NAME} --type=merge -p '{\"spec\":{\"analysis\":{\"iterations\":0}}}' && kubectl rollout undo deployment/fitbuddy-app -n ${NAMESPACE}"
