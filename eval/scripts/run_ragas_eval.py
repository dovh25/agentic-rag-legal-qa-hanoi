#!/usr/bin/env python3
"""RAGAS Evaluation Script for Agentic RAG Legal QA System.

This script evaluates the system using RAGAS metrics:
- Faithfulness
- Answer Relevancy
- Context Recall
- Context Precision

Requires: ragas, datasets, and an LLM for evaluation (Groq/OpenAI compatible).
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datasets import Dataset
from langchain_groq import ChatGroq
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

from src.agent.graph import create_agent_graph
from src.core.config import get_settings
from src.core.logging import logger


async def run_agent_query(query: str, as_of_date: str = None, district: str = None) -> dict[str, Any]:
    """Run a query through the agent and return result with contexts."""
    graph = create_agent_graph()
    initial_state = {
        "query": query,
        "as_of_date": as_of_date,
        "district": district,
        "reasoning_steps": [],
    }
    result = await asyncio.to_thread(graph.invoke, initial_state)
    return result


def load_golden_dataset(dataset_path: str = "eval/datasets/golden_questions.jsonl") -> list[dict]:
    """Load golden dataset from JSONL file."""
    path = Path(dataset_path)
    if not path.exists():
        logger.error(f"Dataset not found at {dataset_path}")
        return []

    data = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


async def prepare_ragas_dataset(golden_data: list[dict], max_samples: int = 50) -> Dataset:
    """Prepare dataset in RAGAS format by running queries through the agent."""
    questions = []
    answers = []
    contexts = []
    ground_truths = []

    for i, item in enumerate(golden_data[:max_samples]):
        logger.info(f"Processing {i+1}/{min(len(golden_data), max_samples)}: {item['id']}")

        try:
            result = await run_agent_query(
                query=item["query"],
                as_of_date=item.get("as_of_date"),
                district=item.get("district"),
            )

            # Extract contexts from citations
            retrieved_contexts = []
            for cit in result.get("citations", []):
                ctx = f"{cit.get('document_title', '')} - {cit.get('article_ref', '')} {cit.get('clause', '')}: {cit.get('snippet', '')}"
                retrieved_contexts.append(ctx)

            # Ground truth from gold citations
            gold_contexts = []
            for doc_id in item.get("gold_doc_ids", []):
                gold_contexts.append(f"Expected document: {doc_id}")

            questions.append(item["query"])
            answers.append(result.get("answer", ""))
            contexts.append(retrieved_contexts)
            ground_truths.append(gold_contexts)

        except Exception as e:
            logger.error(f"Error processing {item['id']}: {e}")
            questions.append(item["query"])
            answers.append("")
            contexts.append([])
            ground_truths.append([])

    # Create HuggingFace Dataset
    dataset_dict = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    }

    return Dataset.from_dict(dataset_dict)


def run_ragas_evaluation(dataset: Dataset) -> dict:
    """Run RAGAS evaluation on the dataset."""
    settings = get_settings()

    # Use Groq for RAGAS LLM judge
    if not settings.OPENAI_API_KEY:
        logger.warning("No OPENAI_API_KEY set, using mock evaluation")
        return {
            "faithfulness": 0.0,
            "answer_relevancy": 0.0,
            "context_recall": 0.0,
            "context_precision": 0.0,
            "note": "Mock evaluation - no LLM judge configured"
        }

    # Configure Groq LLM for RAGAS
    eval_llm = ChatGroq(
        groq_api_key=settings.OPENAI_API_KEY,
        model_name=settings.MODEL_NAME,
        temperature=0,
    )

    # Define metrics
    metrics = [
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision,
    ]

    # Run evaluation
    logger.info("Running RAGAS evaluation...")
    results = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=eval_llm,
    )

    return results.to_pandas().mean().to_dict()


async def main():
    """Main evaluation pipeline."""
    logger.info("Starting RAGAS evaluation pipeline")

    # Load golden dataset
    golden_data = load_golden_dataset()
    if not golden_data:
        logger.error("No golden dataset found")
        return 1

    logger.info(f"Loaded {len(golden_data)} golden questions")

    # Prepare RAGAS dataset
    dataset = await prepare_ragas_dataset(golden_data, max_samples=50)
    logger.info(f"Prepared dataset with {len(dataset)} samples")

    # Run RAGAS evaluation
    results = run_ragas_evaluation(dataset)

    # Print results
    logger.info("=== RAGAS Evaluation Results ===")
    for metric, value in results.items():
        logger.info(f"{metric}: {value:.4f}")

    # Check against thresholds
    thresholds = {
        "faithfulness": 0.90,
        "answer_relevancy": 0.85,
        "context_recall": 0.85,
        "context_precision": 0.80,
    }

    passed = True
    for metric, threshold in thresholds.items():
        value = results.get(metric, 0)
        status = "PASS" if value >= threshold else "FAIL"
        if value < threshold:
            passed = False
        logger.info(f"{metric}: {value:.4f} (threshold: {threshold}) - {status}")

    # Save results
    output_path = Path("eval/results/ragas_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved to {output_path}")

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
