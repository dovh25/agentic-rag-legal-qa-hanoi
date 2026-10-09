import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    single_hop: { executor: "constant-vus", vus: 5, duration: "30s", exec: "query" },
    multi_hop: { executor: "constant-vus", vus: 2, duration: "30s", exec: "multiHop" },
  },
  thresholds: { http_req_failed: ["rate<0.01"], http_req_duration: ["p(95)<15000"] },
};

const baseUrl = __ENV.BASE_URL || "https://agentic-rag-legal-qa-api.onrender.com";
const headers = { "Content-Type": "application/json" };

export function query() {
  const response = http.post(`${baseUrl}/api/v1/query`, JSON.stringify({
    query: "Điều kiện bồi thường khi Nhà nước thu hồi đất tại Hà Nội?",
    district: "Cầu Giấy",
    as_of_date: "2026-10-09",
  }), { headers });
  check(response, { "single-hop HTTP 200": (item) => item.status === 200 });
  sleep(1);
}

export function multiHop() {
  const response = http.post(`${baseUrl}/api/v1/query`, JSON.stringify({
    query: "So sánh Luật Đất đai 2024 và Quyết định 61 về tái định cư tại Hà Nội.",
    as_of_date: "2026-10-09",
  }), { headers });
  check(response, { "multi-hop HTTP 200": (item) => item.status === 200 });
  sleep(1);
}
