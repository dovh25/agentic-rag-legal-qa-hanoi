# Week 2–3 acceptance evidence

**Status checked:** 2026-10-08
**Decision:** Not accepted as 100% complete. The local code gates below pass; several mandatory production, corpus, legal-review, availability, and user-study gates do not have passing evidence.

## Verified evidence

| Gate | Result | Evidence / remaining limit |
|---|---|---|
| Agent/API implementation and regressions | Pass locally | `pytest -q`: 62 passed; `ruff check .`: passed. |
| Frontend build and dependency audit | Pass locally | `cd web && npm run build`: passed; `npm audit --audit-level=high`: 0 vulnerabilities. |
| Current smoke set | Pass locally | `mvp_smoke_20.jsonl`: 20/20; status accuracy 1.0; route accuracy 1.0; Recall@5 1.0; abstention precision 1.0; grounded-citation rate 1.0. Run used deterministic local corpus fallback with cloud credentials absent. |
| Citation and RAGAS metrics | Not measured | Existing smoke set has no lawyer-reviewed article/clause gold labels. No RAGAS model evaluation ran; reported citation accuracy and RAGAS values are `null`, not inferred from smoke pass. |
| Live API basic health | Pass at observation time | `GET /api/v1/health` returned HTTP 200, Qdrant `connected`, LLM `configured`, corpus size 81. This does not validate collection embedding compatibility with the new 768-dimensional contract. |
| Live legal query | Partial / performance concern | One unauthenticated query returned HTTP 200 and cited Điều 14 of Quyết định 61/2024/QĐ-UBND. Observed request time was 11.49 seconds, exceeding the single-hop 8-second target for this sample. One request is not a P95 measurement. |
| Production API authentication | Fail / not deployed | The live query succeeded without `X-API-Key`. New auth code is only local; Render/Vercel deployment secrets were not configured here. |
| Embedding and collection migration | Blocked | Code defaults to `gemini-embedding-001`/768 and `legal_chunks_gemini_embedding_001_v1`; live collection dimensions and re-embedded data have not been verified. Never point this code at the legacy 1024-dimensional `legal_chunks` collection. |
| Ingest P1/P2 | Blocked | Verified official text, OCR review, and source provenance are not available for all required documents. |
| Load and availability | Not measured | k6 script exists but k6 is unavailable locally; no dedicated staging run or continuous three-day uptime record. |
| UX accessibility and SUS | Not measured | No 10-person pilot or SUS results. A successful production build does not constitute user-study evidence. |
| CI | Added, not yet evidenced remotely | GitHub Actions workflow is present; no run result for the new workflow was observed during this check. |

## Implemented code gates

- Gemini query/document embeddings share an explicit model/dimension contract; embedding and collection mismatches fail explicitly.
- Production retrieval no longer uses the offline seed matcher when Qdrant is unavailable or errors.
- Explicit multi-document questions retrieve per requested document and abstain if any requested source is absent. Historical comparison cases requiring the unavailable 2013 law expect abstention.
- Query and feedback endpoints support `X-API-Key`; production fails closed without the key. In-memory per-process rate limiting defaults to 30 requests per 60 seconds.
- The browser calls the same-origin Next.js proxy; the proxy can attach a server-only key and bounds request bodies.
- Ingestion rejects missing registered sources, missing text, empty parse/chunk results, and incomplete indexing.
- Added deterministic evaluator, CI definition, security/deployment runbook, and 50-VU k6 script.

## Required gates before claiming completion

1. Configure production secrets on Render and Vercel; deploy the auth-enabled backend and server proxy, then verify unauthenticated rejection and authenticated UI success.
2. Re-embed the verified P0 corpus into a staging versioned collection, check vector dimension/count/provenance and gold retrieval, then switch production with rollback available.
3. Complete official-source-verified P1/P2 corpus and article-level amendment/validity metadata.
4. Obtain expert-reviewed 50-question gold data with exact document/article/clause labels; run citation, faithfulness, relevancy, abstention, and RAGAS acceptance thresholds.
5. Run k6 against isolated staging and measure single-hop/multi-hop P95 and vector-search latency; monitor the stable deployment continuously for three days.
6. Conduct accessibility review and 10-user pilot; calculate SUS and address blockers.
7. Review CI results and perform final deployed end-to-end smoke before release sign-off.

The checks above require credentials, source material, a staging environment, sustained monitoring, or human participants. Local code changes alone cannot supply that evidence.
