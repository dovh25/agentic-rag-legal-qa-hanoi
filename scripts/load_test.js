/**
 * k6 Load Test Script for Agentic RAG Legal QA API
 * 
 * Run with: k6 run scripts/load_test.js
 * 
 * Targets:
 * - Single-hop P95 ≤ 8s
 * - Multi-hop P95 ≤ 15s
 * - 50 concurrent users
 * - Error rate < 0.5%
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const singleHopLatency = new Trend('single_hop_latency');
const multiHopLatency = new Trend('multi_hop_latency');
const clarificationLatency = new Trend('clarification_latency');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Ramp up to 10 users
    { duration: '1m', target: 25 },    // Ramp up to 25 users
    { duration: '2m', target: 50 },    // Ramp up to 50 users (target)
    { duration: '3m', target: 50 },    // Stay at 50 users
    { duration: '30s', target: 0 },    // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<8000'],           // Single-hop P95 < 8s
    'single_hop_latency': ['p(95)<8000'],
    'multi_hop_latency': ['p(95)<15000'],
    'errors': ['rate<0.005'],                       // Error rate < 0.5%
    'http_req_failed': ['rate<0.01'],              // HTTP error rate < 1%
  },
};

// Base URL - can be overridden via environment variable
const BASE_URL = __ENV.BASE_URL || 'https://agentic-rag-legal-qa-api.onrender.com';
const API_KEY = __ENV.API_KEY || '';

// Test queries for different scenarios
const singleHopQueries = [
  'Hạn mức giao đất ở tại quận Cầu Giấy theo quy định mới nhất?',
  'Bảng giá đất tại quận Ba Đình theo Nghị quyết 52/2025?',
  'Quy định bồi thường khi thu hồi đất nông nghiệp tại Hà Nội?',
  'Điều kiện được tái định cư tại huyện Đông Anh?',
  'Quy định về thu hồi đất để phát triển kinh tế xã hội?',
];

const multiHopQueries = [
  'So sánh bồi thường thu hồi đất theo Luật Đất đai 2024 và Quyết định 61/2024 của Hà Nội',
  'Đối chiếu bảng giá đất Hà Nội với quy định khung giá đất quốc gia',
  'So sánh quy định tái định cư trong Luật Đất đai và Nghị định 88/2024',
];

const clarificationQueries = [
  'đất nông nghiệp',
  'giá đất',
  'tôi bị thu hồi đất',
  'hỏi về tái định cư',
];

function getHeaders() {
  const headers = {
    'Content-Type': 'application/json',
  };
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }
  return headers;
}

function queryEndpoint(query, asOfDate = null, district = null) {
  const payload = JSON.stringify({
    query: query,
    as_of_date: asOfDate,
    district: district,
    max_results: 5,
    include_reasoning_steps: false,
  });
  
  const startTime = new Date();
  const response = http.post(`${BASE_URL}/api/v1/query`, payload, {
    headers: getHeaders(),
    timeout: '30s',
  });
  const latency = new Date() - startTime;
  
  return { response, latency };
}

export default function () {
  // Randomly select query type (70% single-hop, 20% multi-hop, 10% clarification)
  const rand = Math.random();
  let query, expectedLatencyMetric;
  
  if (rand < 0.7) {
    // Single-hop
    query = singleHopQueries[Math.floor(Math.random() * singleHopQueries.length)];
    expectedLatencyMetric = singleHopLatency;
  } else if (rand < 0.9) {
    // Multi-hop
    query = multiHopQueries[Math.floor(Math.random() * multiHopQueries.length)];
    expectedLatencyMetric = multiHopLatency;
  } else {
    // Clarification
    query = clarificationQueries[Math.floor(Math.random() * clarificationQueries.length)];
    expectedLatencyMetric = clarificationLatency;
  }
  
  const { response, latency } = queryEndpoint(query);
  
  // Record latency
  expectedLatencyMetric.add(latency);
  
  // Check response
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'has answer or clarification': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status === 'answered' || body.status === 'clarification_needed' || body.status === 'insufficient_evidence';
      } catch {
        return false;
      }
    },
    'has citations when answered': (r) => {
      try {
        const body = JSON.parse(r.body);
        if (body.status === 'answered') {
          return body.citations && body.citations.length > 0;
        }
        return true;
      } catch {
        return false;
      }
    },
  });
  
  errorRate.add(!success);
  
  // Sleep between requests (simulate user think time)
  sleep(Math.random() * 2 + 1); // 1-3 seconds
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'summary.json': JSON.stringify(data, null, 2),
  };
}