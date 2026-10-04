---
name: eval-rag-benchmark
description: >-
  Procedures for running benchmark evaluations, evaluating Retrieval Recall@K,
  Citation Accuracy, Answer Faithfulness, and Abstention precision for the Legal QA agent.
---

# Legal QA RAG Evaluation Skill

This skill outlines how to run, interpret, and extend evaluation benchmarks for the Agentic RAG legal question-answering system, aligned with [docs/PRD.md](../../docs/PRD.md) and [docs/Brief.md](../../docs/Brief.md).

---

## 1. Quick Execution

To run the full evaluation suite against the evaluation dataset:

```bash
make eval
# Or directly:
python -m eval.scripts.run_eval
```

To run unit and integration tests:
```bash
make test
```

---

## 2. Benchmark Dataset Structure

Test questions are located in `eval/datasets/sample_questions.jsonl` (expanding to 50 golden questions for MVP acceptance).
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
      "article_ref": "Điều 14",
      "clause": "Khoản 1"
    }
  ],
  "as_of_date": "2026-10-04",
  "district": "Ba Đình"
}
```

### Required Test Categories (PRD Section 7)
1. **Single-hop**: Simple queries directly answered by one clause in a specific decree or decision.
2. **Multi-hop / Comparative**: Queries requiring cross-referencing between National Law (Luật Đất đai 2024) and Hanoi Decision (Quyết định 61/2024/QĐ-UBND).
3. **Out-of-Corpus / Insufficient Evidence**: Queries that cannot be verified by existing corpus, expected status: `"insufficient_evidence"`.
4. **Vague / Incomplete Input**: Queries missing administrative location or type of land, expected status: `"clarification_needed"`.
5. **Temporal Boundary Cases**: Queries asking about revoked decrees (e.g. Luật 2013) or historical regulations prior to August 1, 2024.

---

## 3. Core Evaluation Metrics & Acceptance Thresholds

Conforming to **PRD Section 7 & 11** and **Brief Section Success Metrics**:

| Metric | Target (MVP) | Method |
|---|---|---|
| **Faithfulness Score (RAGAS)** | ≥ 0.90 | Entailment check between answer claims and retrieved evidence |
| **Citation Accuracy** | ≥ 95% | Fraction of cited articles/clauses that actually entail the statements |
| **Retrieval Recall@5** | ≥ 90% | Percentage of cases where all gold evidence chunks are in top 5 retrieved |
| **Route Accuracy** | ≥ 95% | Ratio of queries routed correctly (`single_hop`, `multi_hop`, `clarification`) |
| **Abstention Precision** | ≥ 98% | Accuracy of returning `insufficient_evidence` when evidence is truly lacking |
| **Hallucination Rate** | ≤ 1.0% | Percentage of ungrounded or fabricated legal articles/clauses |
| **P95 Latency (Single-hop)** | ≤ 8.0s | End-to-end processing time from request to final response |

---

## 4. Failure Diagnosis Runbook

When a test case fails in `run_eval.py`:

1. **Routing Failure**:
   - Check router prompt and classification rules in `src/agent/nodes.py:router_node`.
   - Ensure boundary terms (e.g. comparative queries) trigger `multi_hop`.
2. **Retrieval Failure (Recall < 1.0)**:
   - Check if dense vector or sparse lexical filter excluded relevant district or document tier.
   - Inspect hybrid fusion RRF weights in `src/agent/tools.py`.
3. **Hallucination / Verification Failure**:
   - Inspect `verify_node` logs.
   - If citation verifier rejected valid evidence, adjust the entailment threshold or verify quote substring matching.
