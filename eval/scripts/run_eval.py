import json
import sys
from pathlib import Path

# Add project root to sys.path for standalone script execution
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agent.graph import create_agent_graph  # noqa: E402
from src.core.logging import logger  # noqa: E402


def run_evaluation(dataset_path: str = "eval/datasets/sample_questions.jsonl") -> bool:
    """Run batch evaluation over test dataset questions."""
    path = Path(dataset_path)
    if not path.exists():
        logger.error(f"Dataset not found at {dataset_path}")
        return False

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
            expected_docs = item.get("expected_doc_ids", [])

            logger.info(f"Running Eval [{item['id']}]: '{query}'")
            result = graph.invoke({"query": query, "reasoning_steps": []})

            actual_status = result.get("status")
            status_match = actual_status == expected_status

            citation_match = True
            if expected_docs:
                cited_doc_ids = [c.get("doc_id") for c in result.get("citations", [])]
                citation_match = any(doc_id in cited_doc_ids for doc_id in expected_docs)

            if status_match and citation_match:
                passed += 1
                logger.info(f"✓ Case {item['id']} passed (Status: {actual_status}).")
            else:
                logger.warning(
                    f"✗ Case {item['id']} failed. Expected status: {expected_status}, got: {actual_status}. "
                    f"Expected docs: {expected_docs}, got: {[c.get('doc_id') for c in result.get('citations', [])]}"
                )

    accuracy = (passed / total * 100) if total > 0 else 0
    logger.info(f"Evaluation complete. Result: {passed}/{total} ({accuracy:.1f}%)")
    return passed == total


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)
