"""Run secret-free production endpoint smoke checks and write a JSON report."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import httpx


def run(base_url: str, timeout: float) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout) as client:
        cases = [
            ("health", "GET", "/health", None),
            (
                "query",
                "POST",
                "/api/v1/query",
                {"query": "Quy định bồi thường khi thu hồi đất tại Hà Nội?"},
            ),
            (
                "clarification",
                "POST",
                "/api/v1/query",
                {"query": "đất nông nghiệp"},
            ),
            (
                "chat_stream",
                "POST",
                "/api/v1/chat/stream",
                {"message": "Bảng giá đất tại quận Ba Đình?"},
            ),
        ]
        for name, method, path, payload in cases:
            started = time.perf_counter()
            try:
                response = client.request(method, path, json=payload)
                elapsed = round((time.perf_counter() - started) * 1000, 2)
                checks.append(
                    {
                        "name": name,
                        "status_code": response.status_code,
                        "latency_ms": elapsed,
                        "passed": response.status_code == 200,
                        "content_type": response.headers.get("content-type", ""),
                        "sse_completion": (
                            "message_completed" in response.text if name == "chat_stream" else None
                        ),
                    }
                )
            except httpx.HTTPError as error:
                checks.append({"name": name, "passed": False, "error": type(error).__name__})
    return {
        "base_url": base_url,
        "checks": checks,
        "passed": all(item["passed"] for item in checks),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://agentic-rag-legal-qa-api.onrender.com")
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--output", default="artifacts/production-smoke.json")
    args = parser.parse_args()
    report = run(args.base_url, args.timeout)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
