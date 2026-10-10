"""Prometheus metrics definitions for the Legal QA system."""

from prometheus_client import Counter, Histogram

# HTTP metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

# Legal query metrics
QUERY_LATENCY = Histogram(
    "legal_query_duration_seconds",
    "Legal query processing latency in seconds",
    ["route", "status"],
)
QUERY_COUNT = Counter(
    "legal_queries_total",
    "Total legal queries processed",
    ["route", "status"],
)