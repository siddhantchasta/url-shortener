import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    redirect_hot_path: {
      executor: 'constant-vus',
      vus: 50,
      duration: '30s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<200'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const SHORT_CODE = __ENV.SHORT_CODE; // create one first, pass it in via env

export default function () {
  const res = http.get(`${BASE_URL}/${SHORT_CODE}`, { redirects: 0 });
  check(res, { 'status is 307': (r) => r.status === 307 });
  sleep(0.1);
}
