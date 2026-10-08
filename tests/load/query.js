import http from "k6/http";
import { check } from "k6";
import { Trend } from "k6/metrics";

const singleHopDuration = new Trend("single_hop_request_duration", true);
const multiHopDuration = new Trend("multi_hop_request_duration", true);
const validResponse = new Trend("valid_legal_qa_response", true);

export const options = {
  vus: Number(__ENV.VUS || 50),
  duration: __ENV.DURATION || "5m",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    valid_legal_qa_response: ["rate>0.99"],
    single_hop_request_duration: ["p(95)<8000"],
    multi_hop_request_duration: ["p(95)<15000"],
  },
};

const singleHopQuery = {
  query: "Hạn mức giao đất ở tại Hà Nội theo Quyết định 61/2024/QĐ-UBND?",
  as_of_date: "2026-10-08",
  district: "Cầu Giấy",
  max_results: 5,
};

const multiHopQuery = {
  query:
    "So sánh quy định bồi thường đất nông nghiệp theo Luật Đất đai 2024 và Nghị định 88/2024/NĐ-CP tại Hà Nội",
  as_of_date: "2026-10-08",
  district: "Đông Anh",
  max_results: 5,
};

export default function () {
  if (!__ENV.BASE_URL) {
    throw new Error("Set BASE_URL to the dedicated staging API URL.");
  }

  const isMultiHop = (__VU + __ITER) % 2 === 0;
  const query = isMultiHop ? multiHopQuery : singleHopQuery;
  const metric = isMultiHop ? multiHopDuration : singleHopDuration;
  const headers = { "Content-Type": "application/json" };
  if (__ENV.API_KEY) {
    headers["X-API-Key"] = __ENV.API_KEY;
  }
  const response = http.post(
    `${__ENV.BASE_URL.replace(/\/$/, "")}/api/v1/query`,
    JSON.stringify(query),
    { headers, timeout: "60s", tags: { flow: isMultiHop ? "multi_hop" : "single_hop" } },
  );
  metric.add(response.timings.duration);
  const valid = check(response, {
    "HTTP 200": (res) => res.status === 200,
    "legal QA response has a supported status": (res) => {
      if (res.status !== 200) return false;
      try {
        const body = res.json();
        return ["answered", "insufficient_evidence", "clarification_needed"].includes(
          body.status,
        );
      } catch {
        return false;
      }
    },
  });
  validResponse.add(valid);
}
