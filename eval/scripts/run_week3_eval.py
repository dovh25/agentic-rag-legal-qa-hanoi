"""Run reproducible Week 3 evaluation and emit a secret-free JSON report."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agent.graph import create_agent_graph  # noqa: E402


def _load_cases(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def evaluate(dataset: Path) -> dict[str, Any]:
    graph = create_agent_graph()
    results: list[dict[str, Any]] = []
    for case in _load_cases(dataset):
        started = time.perf_counter()
        output = graph.invoke(
            {
                "query": case["query"],
                "as_of_date": case.get("as_of_date"),
                "district": case.get("district"),
                "reasoning_steps": [],
            }
        )
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        cited = {item.get("doc_id") for item in output.get("citations", [])}
        retrieved = {item.get("doc_id") for item in output.get("retrieved_documents", [])[:5]}
        gold = set(case.get("gold_doc_ids", []))
        results.append(
            {
                "id": case["id"],
                "category": case.get("category", "legacy"),
                "expected_status": case["expected_status"],
                "actual_status": output.get("status"),
                "expected_route": case.get("expected_route"),
                "actual_route": output.get("route"),
                "status_match": output.get("status") == case["expected_status"],
                "route_match": (
                    case.get("expected_route") is None
                    or output.get("route") == case["expected_route"]
                ),
                "gold_doc_ids": sorted(gold),
                "cited_doc_ids": sorted(cited),
                "recall_at_5_match": not gold or gold.issubset(retrieved),
                "citation_count": len(output.get("citations", [])),
                "latency_ms": latency_ms,
            }
        )
    total = len(results)
    return {
        "dataset": str(dataset),
        "total": total,
        "status_accuracy": sum(item["status_match"] for item in results) / total if total else 0,
        "route_accuracy": sum(item["route_match"] for item in results) / total if total else 0,
        "recall_at_5_proxy": sum(item["recall_at_5_match"] for item in results) / total
        if total
        else 0,
        "latency_ms": {
            "p50": _percentile([item["latency_ms"] for item in results], 0.50),
            "p95": _percentile([item["latency_ms"] for item in results], 0.95),
        },
        "by_category": dict(Counter(item["category"] for item in results)),
        "ragas": {"status": "not_measured", "reason": "RAGAS judge pipeline is not configured"},
        "results": results,
    }


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * quantile))
    return ordered[index]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="eval/datasets/golden_questions.jsonl")
    parser.add_argument("--output", default="artifacts/week3-eval.json")
    args = parser.parse_args()
    report = evaluate(Path(args.dataset))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "results"}, ensure_ascii=False
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
