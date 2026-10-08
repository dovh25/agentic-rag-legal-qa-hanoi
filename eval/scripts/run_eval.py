import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path
from typing import Any

# Add project root to sys.path for standalone script execution
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agent.graph import create_agent_graph  # noqa: E402
from src.core.logging import logger  # noqa: E402

VALID_STATUSES = {"answered", "clarification_needed", "insufficient_evidence"}


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").casefold().split())


def _load_dataset(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}")

    cases = []
    seen_ids = set()
    with path.open(encoding="utf-8") as dataset:
        for line_number, line in enumerate(dataset, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Expected a JSON object on line {line_number}.")
            for field in ("id", "query", "expected_status"):
                if not item.get(field):
                    raise ValueError(f"Missing '{field}' on line {line_number}.")
            if item["expected_status"] not in VALID_STATUSES:
                raise ValueError(
                    f"Invalid expected_status on line {line_number}: {item['expected_status']}"
                )
            if item.get("expected_route") not in (
                None,
                "single_hop",
                "multi_hop",
                "clarification",
            ):
                raise ValueError(f"Invalid expected_route on line {line_number}.")
            if item.get("as_of_date") is not None:
                try:
                    parsed_date = date.fromisoformat(item["as_of_date"])
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"Invalid as_of_date on line {line_number}.") from exc
                if parsed_date.isoformat() != item["as_of_date"]:
                    raise ValueError(f"Invalid as_of_date on line {line_number}.")
            if item["id"] in seen_ids:
                raise ValueError(f"Duplicate case id '{item['id']}' on line {line_number}.")
            if not isinstance(item.get("expected_doc_ids", []), list):
                raise ValueError(f"expected_doc_ids must be a list on line {line_number}.")
            if not isinstance(item.get("gold_citations", []), list):
                raise ValueError(f"gold_citations must be a list on line {line_number}.")
            for citation in item.get("gold_citations", []):
                if (
                    not isinstance(citation, dict)
                    or not (citation.get("doc_id") or citation.get("doc_number"))
                    or not citation.get("article_ref")
                ):
                    raise ValueError(
                        f"Each gold citation needs a document identifier and article_ref "
                        f"(line {line_number})."
                    )
            seen_ids.add(item["id"])
            cases.append(item)

    if not cases:
        raise ValueError(f"Dataset at {path} contains no cases.")
    return cases


def _matches_gold_citation(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    comparisons = {
        "doc_id": ("doc_id",),
        "doc_number": ("document_number", "doc_number"),
        "article_ref": ("article_ref", "article"),
        "clause": ("clause",),
    }
    for expected_key, actual_keys in comparisons.items():
        expected_value = expected.get(expected_key)
        if expected_value is None:
            continue
        if not any(
            _normalize(actual.get(key)) == _normalize(expected_value) for key in actual_keys
        ):
            return False
    return True


def _percentile_95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def evaluate_dataset(
    dataset_path: str = "eval/datasets/mvp_smoke_20.jsonl",
    graph: Any | None = None,
) -> dict[str, Any]:
    """Evaluate route, status, gold retrieval/citations, abstention and latency."""
    cases = _load_dataset(Path(dataset_path))
    graph = graph or create_agent_graph()
    case_results = []
    status_correct = 0
    route_total = 0
    route_correct = 0
    expected_targets = 0
    retrieved_targets = 0
    gold_citation_total = 0
    gold_citation_hits = 0
    labelled_citations_total = 0
    labelled_citations_correct = 0
    predicted_abstentions = 0
    correct_abstentions = 0
    citations_total = 0
    grounded_citations = 0
    latencies = []
    passed = 0

    for item in cases:
        logger.info(f"Running Eval [{item['id']}]: '{item['query']}'")
        graph_input = {
            "query": item["query"],
            "as_of_date": item.get("as_of_date"),
            "district": item.get("district"),
            "reasoning_steps": [],
        }
        if item.get("max_results") is not None:
            graph_input["max_results"] = item["max_results"]
        result = graph.invoke(graph_input)
        actual_status = result.get("status")
        actual_route = result.get("route")
        citations = result.get("citations") or []
        retrieved = (result.get("retrieved_documents") or [])[:5]
        status_match = actual_status == item["expected_status"]
        route_match = item.get("expected_route") is None or actual_route == item.get(
            "expected_route"
        )

        if item.get("expected_route") is not None:
            route_total += 1
            route_correct += int(route_match)
        status_correct += int(status_match)

        gold_citations = item.get("gold_citations", [])
        expected_doc_ids = item.get("expected_doc_ids", [])
        if gold_citations:
            gold_citation_total += len(gold_citations)
            for expected in gold_citations:
                found_in_retrieval = any(
                    _matches_gold_citation(document, expected) for document in retrieved
                )
                found_in_citations = any(
                    _matches_gold_citation(citation, expected) for citation in citations
                )
                expected_targets += 1
                retrieved_targets += int(found_in_retrieval)
                gold_citation_hits += int(found_in_citations)
            labelled_citations_total += len(citations)
            labelled_citations_correct += sum(
                any(_matches_gold_citation(citation, expected) for expected in gold_citations)
                for citation in citations
            )
            citation_match = all(
                any(_matches_gold_citation(citation, expected) for citation in citations)
                for expected in gold_citations
            )
        else:
            citation_match = all(
                any(citation.get("doc_id") == expected_doc_id for citation in citations)
                for expected_doc_id in expected_doc_ids
            )
            expected_targets += len(expected_doc_ids)
            retrieved_targets += sum(
                any(document.get("doc_id") == expected_doc_id for document in retrieved)
                for expected_doc_id in expected_doc_ids
            )

        if actual_status == "insufficient_evidence":
            predicted_abstentions += 1
            correct_abstentions += int(item["expected_status"] == "insufficient_evidence")

        evidence_keys = {
            (
                _normalize(document.get("doc_id")),
                _normalize(document.get("article_ref") or document.get("article")),
                _normalize(document.get("clause")),
            )
            for document in result.get("retrieved_documents", [])
        }
        citations_total += len(citations)
        grounded_citations += sum(
            (
                _normalize(citation.get("doc_id")),
                _normalize(citation.get("article_ref") or citation.get("article")),
                _normalize(citation.get("clause")),
            )
            in evidence_keys
            for citation in citations
        )

        latency = result.get("processing_time_ms")
        if isinstance(latency, (int, float)):
            latencies.append(float(latency))

        case_passed = status_match and route_match and citation_match
        passed += int(case_passed)
        case_results.append(
            {
                "id": item["id"],
                "passed": case_passed,
                "expected_status": item["expected_status"],
                "actual_status": actual_status,
                "expected_route": item.get("expected_route"),
                "actual_route": actual_route,
                "gold_citation_match": citation_match,
                "cited_doc_ids": sorted(
                    {str(citation.get("doc_id", "")) for citation in citations}
                ),
            }
        )

    return {
        "dataset": str(dataset_path),
        "total_cases": len(cases),
        "passed_cases": passed,
        "status_accuracy": status_correct / len(cases),
        "route_accuracy": route_correct / route_total if route_total else None,
        "retrieval_recall_at_5": (
            retrieved_targets / expected_targets if expected_targets else None
        ),
        "gold_citation_recall": (
            gold_citation_hits / gold_citation_total if gold_citation_total else None
        ),
        "citation_accuracy": (
            labelled_citations_correct / labelled_citations_total
            if labelled_citations_total
            else None
        ),
        "abstention_precision": (
            correct_abstentions / predicted_abstentions if predicted_abstentions else None
        ),
        "grounded_citation_rate": (
            grounded_citations / citations_total if citations_total else None
        ),
        "p95_latency_ms": _percentile_95(latencies),
        "ragas_scores": None,
        "ragas_note": (
            "Not measured by this deterministic evaluator; requires a reviewed gold set "
            "and an explicitly configured RAGAS run."
        ),
        "cases": case_results,
    }


def run_evaluation(
    dataset_path: str = "eval/datasets/mvp_smoke_20.jsonl",
    output_path: str | None = None,
) -> bool:
    """Run evaluation, log measured metrics, and optionally persist a JSON report."""
    report = evaluate_dataset(dataset_path)
    logger.info(
        "Evaluation: "
        f"{report['passed_cases']}/{report['total_cases']} cases; "
        f"status accuracy={report['status_accuracy']:.3f}; "
        f"route accuracy={report['route_accuracy']}; "
        f"Recall@5={report['retrieval_recall_at_5']}; "
        f"gold citation recall={report['gold_citation_recall']}; "
        f"gold-labelled citation accuracy={report['citation_accuracy']}; "
        f"abstention precision={report['abstention_precision']}; "
        f"grounded citation rate={report['grounded_citation_rate']}; "
        f"P95={report['p95_latency_ms']} ms"
    )
    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return report["passed_cases"] == report["total_cases"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the Legal QA agent.")
    parser.add_argument(
        "--dataset",
        default="eval/datasets/mvp_smoke_20.jsonl",
        help="JSONL evaluation dataset path.",
    )
    parser.add_argument("--output", help="Optional path for a JSON metrics report.")
    args = parser.parse_args()
    success = run_evaluation(args.dataset, args.output)
    sys.exit(0 if success else 1)
