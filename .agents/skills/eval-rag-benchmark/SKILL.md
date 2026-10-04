---
name: eval-rag-benchmark
description: >-
  Procedures for running benchmark evaluations, evaluating Retrieval Recall@K,
  Citation Accuracy, Answer Faithfulness, and Abstention precision for the Legal QA agent.
---

# Legal QA RAG Evaluation Skill

This skill outlines how to run, interpret, and extend evaluation benchmarks for the Agentic RAG legal question-answering system.

---

## 1. Quick Execution

To run the full evaluation suite against the evaluation dataset:

```bash
make eval
# Or directly via Python:
python eval/scripts/run_eval.py
```

To run unit and integration tests:
```bash
make test
```

---

## 2. Benchmark Dataset Structure

Test questions are located in `eval/datasets/sample_questions.jsonl`.
Each test case must follow this schema:

```json
{
  "id": "TC_001",
  "query": "Hạn mức giao đất ở tại quận Ba Đình theo quy định mới nhất là bao nhiêu?",
  "category": "single_hop",
  "expected_route": "single_hop",
  "expected_status": "answered",
  "gold_citations": [
    {
      "doc_number": "61/2024/QĐ-UBND",
      "article": "14",
      "clause": "1"
    }
  ],
  "as_of_date": "2026-10-04"
}
```

### Required Test Categories
1. **Single-hop**: Simple queries directly answered by one clause in a specific decree or decision.
2. **Multi-hop / Comparative**: Queries requiring cross-referencing between National Law (Luật Đất đai 2024) and Hanoi Decision (Quyết định 61/2024/QĐ-UBND).
3. **Out-of-Corpus / Insufficient Evidence**: Queries that cannot be verified by existing corpus, expected status: `"insufficient_evidence"`.
4. **Vague / Incomplete Input**: Queries missing administrative location or type of land, expected status: `"clarification_needed"`.
5. **Temporal Boundary Cases**: Queries asking about revoked decrees or historical regulations prior to August 1, 2024.

---

## 3. Core Evaluation Metrics

| Metric | Target | Description |
|---|---|---|
| **Route Accuracy** | ≥ 95% | Ratio of queries routed correctly (`single_hop`, `multi_hop`, `clarification`). |
| **Retrieval Recall@5** | ≥ 90% | Percentage of cases where all gold evidence chunks are in top 5 retrieved. |
| **Citation Accuracy** | ≥ 95% | Fraction of cited articles/clauses that actually entail the statements made. |
| **Faithfulness (Groundedness)** | ≥ 92% | Absence of ungrounded or hallucinated claims. |
| **Abstention Precision** | ≥ 98% | Accuracy of returning `insufficient_evidence` when evidence is truly lacking. |

---

## 4. Failure Diagnosis Runbook

When a test case fails in `run_eval.py`:

1. **Routing Failure**:
   - Check router prompt and classification rules in `src/agent/nodes.py:router_node`.
   - Ensure boundary terms (e.g., questions with comparison keywords like "khác nhau giữa") trigger `multi_hop`.
2. **Retrieval Failure (Recall < 1.0)**:
   - Check if dense vector or sparse lexical filter excluded relevant district or document tier.
   - Inspect hybrid fusion RRF weights in `src/agent/tools.py`.
3. **Hallucination / Verification Failure**:
   - Inspect `verify_node` logs.
   - If citation verifier rejected valid evidence, adjust the entailment threshold or verify quote substring matching.
