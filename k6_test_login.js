import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    // A number of virtual users to run concurrently
    vus: 10,
    // The duration of the test
    duration: '30s',
    thresholds: {
        http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
        http_req_failed: ['rate<0.1'],   // Error rate should be less than 10%
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5000/api';

export default function () {
    const payload = JSON.stringify({
        username: 'superadmin',
        password: 'super123',
        tenant_slug: ''
    });

    const params = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const res = http.post(`${BASE_URL}/auth/login`, payload, params);

    check(res, {
        'is status 200 or 401': (r) => r.status === 200 || r.status === 401,
        // Uncomment the following if you want to strictly check for successful logins
        // 'login successful': (r) => r.status === 200,
        // 'has access token': (r) => JSON.parse(r.body).access_token !== undefined,
    });

    sleep(1);
}
