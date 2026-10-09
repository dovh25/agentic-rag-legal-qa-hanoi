import json
from pathlib import Path

from eval.scripts.run_week3_eval import _percentile


def test_golden_dataset_has_fifty_categorized_cases():
    path = Path("eval/datasets/golden_questions.jsonl")
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(cases) == 50
    assert {case["category"] for case in cases} == {
        "single_hop",
        "multi_hop",
        "clarification",
        "out_of_corpus",
        "temporal_boundary",
    }
    assert len({case["id"] for case in cases}) == 50


def test_percentile_is_deterministic():
    assert _percentile([10, 20, 30, 40, 50], 0.50) == 30
    assert _percentile([], 0.95) is None
