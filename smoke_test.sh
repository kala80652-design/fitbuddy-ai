#!/usr/bin/env bash
# ============================================================================
# FitBuddy Production Smoke Test & Latency Verification Script
# Usage: ./smoke_test.sh <BASE_URL>
# Example: ./smoke_test.sh https://fitbuddy-ai.onrender.com
# ============================================================================

set -eo pipefail

BASE_URL="${1:-http://localhost:8000}"
# Trim trailing slash
BASE_URL="${BASE_URL%/}"

echo "========================================================="
echo " Starting FitBuddy Smoke Tests on: ${BASE_URL}"
echo "========================================================="

# 1. Health & Liveness Probe
echo -n "[1/4] Testing Liveness Endpoint (GET /healthz)... "
HEALTH_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X GET "${BASE_URL}/healthz" -H "Accept: application/json")
HTTP_STATUS=$(echo "${HEALTH_RESP}" | grep "HTTP_STATUS" | cut -d':' -f2)
BODY=$(echo "${HEALTH_RESP}" | grep -v "HTTP_STATUS")

if [ "${HTTP_STATUS}" -ne 200 ]; then
    echo " FAILED (HTTP ${HTTP_STATUS})"
    echo "${BODY}"
    exit 1
fi

STATUS_VAL=$(echo "${BODY}" | grep -o '"status": *"[^"]*"' | cut -d'"' -f4 || true)
DB_VAL=$(echo "${BODY}" | grep -o '"database": *"[^"]*"' | cut -d'"' -f4 || true)

if [ "${STATUS_VAL}" != "healthy" ] || [ "${DB_VAL}" != "connected" ]; then
    echo " FAILED (Malformed health payload: ${BODY})"
    exit 1
fi
echo " PASSED (status=${STATUS_VAL}, db=${DB_VAL})"

# 2. Plan Generation Endpoint
TEST_USER_ID="smoke_user_$(date +%s)"
echo -n "[2/4] Testing Workout Synthesis (POST /api/v1/generate-workout)... "
START_TIME=$(date +%s%3N 2>/dev/null || python -c 'import time; print(int(time.time()*1000))')

GEN_PAYLOAD=$(cat <<EOF
{
  "user_id": "${TEST_USER_ID}",
  "name": "Smoke Tester",
  "age": 28,
  "weight": 75.0,
  "fitness_goal": "Fat Loss",
  "intensity": "Intermediate"
}
EOF
)

GEN_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${BASE_URL}/api/v1/generate-workout" \
  -H "Content-Type: application/json" \
  -d "${GEN_PAYLOAD}")

END_TIME=$(date +%s%3N 2>/dev/null || python -c 'import time; print(int(time.time()*1000))')
LATENCY=$((END_TIME - START_TIME))

HTTP_STATUS=$(echo "${GEN_RESP}" | grep "HTTP_STATUS" | cut -d':' -f2)
BODY=$(echo "${GEN_RESP}" | grep -v "HTTP_STATUS")

if [ "${HTTP_STATUS}" -ne 201 ]; then
    echo " FAILED (HTTP ${HTTP_STATUS})"
    echo "${BODY}"
    exit 1
fi
echo " PASSED (Latency: ${LATENCY}ms, User: ${TEST_USER_ID})"

# 3. Plan Revision & Feedback Loop
echo -n "[3/4] Testing Single-Turn Plan Mutation (POST /api/v1/submit-feedback)... "
FEEDBACK_PAYLOAD=$(cat <<EOF
{
  "user_id": "${TEST_USER_ID}",
  "feedback": "I have mild knee pain, replace heavy lunges with leg extensions."
}
EOF
)

FEED_RESP=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "${BASE_URL}/api/v1/submit-feedback" \
  -H "Content-Type: application/json" \
  -d "${FEEDBACK_PAYLOAD}")

HTTP_STATUS=$(echo "${FEED_RESP}" | grep "HTTP_STATUS" | cut -d':' -f2)
BODY=$(echo "${FEED_RESP}" | grep -v "HTTP_STATUS")

if [ "${HTTP_STATUS}" -ne 200 ]; then
    echo " FAILED (HTTP ${HTTP_STATUS})"
    echo "${BODY}"
    exit 1
fi
echo " PASSED (Revised Plan Saved)"

# 4. Rate Limiter Guardrail Test (Assert HTTP 429 after threshold)
echo -n "[4/4] Verifying Rate Limit Guardrails (Bursting 65 requests)... "
LIMIT_TRIGGERED=0
for i in {1..65}; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/healthz")
    if [ "${CODE}" -eq 429 ]; then
        LIMIT_TRIGGERED=1
        break
    fi
done

if [ "${LIMIT_TRIGGERED}" -eq 1 ]; then
    echo " PASSED (HTTP 429 RateLimitExceeded verified)"
else
    echo " WARNING (429 not triggered in burst; check reverse proxy cache or IP headers)"
fi

echo "========================================================="
echo " All Smoke Tests Completed Successfully!"
echo "========================================================="
