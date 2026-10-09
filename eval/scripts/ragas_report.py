"""Create an explicit RAGAS evidence status without fabricating metrics."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    report = {
        "status": "not_measured",
        "metrics": {
            "faithfulness": None,
            "answer_relevancy": None,
            "context_recall": None,
        },
        "reason": "Configure a RAGAS-compatible judge model and dataset outputs before running.",
        "thresholds": {
            "faithfulness": 0.90,
            "answer_relevancy": 0.85,
            "context_recall": 0.85,
        },
    }
    output = Path("artifacts/ragas-report.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
