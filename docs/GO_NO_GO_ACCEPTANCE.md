# Validated MVP Go/No-Go Acceptance Matrix

> Trạng thái: **CONDITIONAL GO candidate** — chưa phải kết luận cuối cho tới khi có
> production evidence và waiver được ghi nhận.

## Hard gates

| Gate | Threshold/evidence | Current status | Required artifact |
|---|---|---|---|
| Official corpus | 5 P0 verified snapshots, validation 0 errors | ✅ Pass | validation report + Qdrant count |
| Citation grounding | URL, document, article/clause and quote match | ⚠️ Pending | 50-case manual audit |
| Abstention | Precision ≥ 98% | ⚠️ Pending | abstention report |
| Prompt-injection safety | No secret/evidence exfiltration | ⚠️ Pending | security report |
| Deploy health | Render/Vercel healthy after current redeploy | ⚠️ Pending | production smoke report |

## Quality targets from PRD

| Metric | Target | Evidence status |
|---|---:|---|
| RAGAS faithfulness | ≥ 0.90 | Not measured |
| RAGAS answer relevancy | ≥ 0.85 | Not measured |
| Context recall / Recall@5 | ≥ 0.85 / ≥ 0.90 | Not measured |
| Citation accuracy | ≥ 95% | Not measured |
| Hallucination rate | ≤ 1% | Not measured |
| P95 single-hop | ≤ 8s | Not measured |
| P95 multi-hop | ≤ 15s | Not measured |
| API uptime | ≥ 99.5% over acceptance window | Not measured |
| SUS | ≥ 75/100 | Not measured |

## Conditional Go policy

Conditional Go may permit a controlled demo only when:

1. No hard safety gate fails.
2. Every missing metric has an owner, risk, mitigation, expiry and explicit approver.
3. The demo script avoids unsupported claims and shows `insufficient_evidence` honestly.
4. The status remains `conditional MVP`, not `validated MVP`, until all required evidence is
   collected.

No waiver is allowed for secret exposure, citation spoofing, uncontrolled hallucination,
prompt-injection data exfiltration, data loss, or an unresponsive production service.

## Required run sequence

1. Run local tests, Ruff, frontend build, API/SSE contract checks and manifest validation.
2. Inject the Mistral key only through secret management; verify provider/model/quota without
   printing the key.
3. Redeploy Render/Vercel and check `/api/v1/health`, `/api/v1/query` and
   `/api/v1/chat/stream`.
4. Run 50-case evaluation, 20+ production smoke cases, load/latency, security and UX/SUS.
5. Attach reports and decide GO, CONDITIONAL GO or NO-GO.
