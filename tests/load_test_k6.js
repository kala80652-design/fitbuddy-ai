import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

// Custom Prometheus Trends & Rates
export const errorRate = new Rate('errors');
export const workoutLatency = new Trend('workout_generation_latency');

export const options = {
  stages: [
    { duration: '3m', target: 500 },   // Ramp-up to 500 VUs
    { duration: '5m', target: 500 },   // Steady-state load
    { duration: '1m', target: 1200 },  // Burst stress spike to 1,200 VUs
    { duration: '2m', target: 0 },     // Ramp-down to 0
  ],
  thresholds: {
    'http_req_duration{status:200}': ['p(95)<800'], // P95 latency < 800ms
    'http_req_failed': ['rate<0.01'],               // Error rate < 1%
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8000';

export default function () {
  const rand = Math.random();

  // Scenario 1: 60% Browsing & Health Check Probes
  if (rand < 0.60) {
    const res = http.get(`${BASE_URL}/healthz`);
    const success = check(res, {
      'healthz status 200': (r) => r.status === 200,
      'db connected': (r) => r.json().database === 'connected',
    });
    errorRate.add(!success);
    sleep(1);
  }
  // Scenario 2: 30% Asynchronous Workout Generation Requests
  else if (rand < 0.90) {
    const userId = `k6_user_${__VU}_${__ITER}`;
    const payload = JSON.stringify({
      user_id: userId,
      name: 'K6 Load Tester',
      age: 29,
      weight: 76.5,
      fitness_goal: 'Muscle Hypertrophy',
      intensity: 'Advanced',
    });

    const headers = { 'Content-Type': 'application/json' };
    const res = http.post(`${BASE_URL}/api/v1/generate-workout`, payload, { headers });
    
    workoutLatency.add(res.timings.duration);
    const success = check(res, {
      'workout generation status 201 or 200': (r) => r.status === 201 || r.status === 200,
      'valid plan returned': (r) => r.json().original_plan !== undefined,
    });
    errorRate.add(!success);
    sleep(2);
  }
  // Scenario 3: 10% Feedback Revisions
  else {
    const feedbackPayload = JSON.stringify({
      user_id: `k6_user_${__VU}_0`,
      feedback: 'Lower intensity slightly due to fatigue.',
    });

    const headers = { 'Content-Type': 'application/json' };
    const res = http.post(`${BASE_URL}/api/v1/submit-feedback`, feedbackPayload, { headers });
    
    const success = check(res, {
      'feedback status 200': (r) => r.status === 200 || r.status === 404,
    });
    errorRate.add(!success);
    sleep(2);
  }
}
