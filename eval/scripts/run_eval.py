import json
import sys
from pathlib import Path

# Add project root to sys.path for standalone script execution
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agent.graph import create_agent_graph  # noqa: E402
from src.core.logging import logger  # noqa: E402


def run_evaluation(dataset_path: str = "eval/datasets/sample_questions.jsonl"):
    """Run batch evaluation over test dataset questions."""
    path = Path(dataset_path)
    if not path.exists():
        logger.error(f"Dataset not found at {dataset_path}")
        return

    graph = create_agent_graph()
    total = 0
    passed = 0

    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            total += 1
            query = item["query"]
            expected_status = item.get("expected_status")

            logger.info(f"Running Eval [{item['id']}]: '{query}'")
            result = graph.invoke({"query": query, "reasoning_steps": []})

            if result.get("status") == expected_status:
                passed += 1
                logger.info(f"✓ Case {item['id']} passed.")
            else:
                logger.warning(
                    f"✗ Case {item['id']} failed. Expected {expected_status}, got {result.get('status')}"
                )

    accuracy = (passed / total * 100) if total > 0 else 0
    logger.info(f"Evaluation complete. Result: {passed}/{total} ({accuracy:.1f}%)")


if __name__ == "__main__":
    run_evaluation()
