# Demo deployment security and load-test runbook

## Configure API authentication

1. Generate one high-entropy API key and store it as a secret in both Render and Vercel. Never put it in `NEXT_PUBLIC_*`, source control, or a client-side bundle.
2. On Render set `ENVIRONMENT=production`, `API_KEY=<secret>`, and `CORS_ORIGINS=https://agentic-rag-legal-qa-hanoi.vercel.app`.
3. On Vercel set server-only `API_KEY=<same secret>` and `API_BASE_URL=https://agentic-rag-legal-qa-api.onrender.com`. Keep `NEXT_PUBLIC_API_BASE_URL` only for the public API documentation link if required.
4. Redeploy both services. Query from the UI through the Next.js `/api/query` server route. Confirm a direct API request without `X-API-Key` returns 401 and the UI still receives the expected response.
5. Confirm `/api/v1/health` remains public for monitoring. Query and feedback endpoints require the key when configured; production fails closed if `API_KEY` is missing.

The API rate limiter defaults to 30 requests per 60 seconds per client IP and is in-memory per process. It is suitable only for the current single-instance demo; it is not a distributed quota and is not a substitute for an edge/API gateway limit when scaling or running multiple instances. Requests proxied by Vercel may share egress identity at Render.

## Safe Qdrant embedding migration

The `legal_chunks` collection is a legacy 1024-dimensional collection. The current code expects `gemini-embedding-001` at 768 dimensions and defaults to `legal_chunks_gemini_embedding_001_v1`.

1. Obtain an approved Google API key and verified legal source corpus. Do not use unverified scans or synthesized legal text.
2. Configure the ingestion environment with `EMBEDDING_API_KEY`, the Qdrant endpoint/key, `EMBEDDING_MODEL=gemini-embedding-001`, `EMBEDDING_DIMENSION=768`, and the versioned collection name.
3. Run `python scripts/run_ingest.py --tier p0` against the staging Qdrant collection. The pipeline must exit non-zero for missing documents/text, parse failures, embedding errors, dimension mismatches, or incomplete upserts.
4. Verify collection dimensions, indexed count, source metadata/checksums, effective-date filters, and gold retrieval cases. Do not point production to an empty or unverified collection.
5. Set Render's `QDRANT_COLLECTION` to the verified versioned collection and redeploy. Keep `legal_chunks` available for rollback.

Embedding sends public legal text and user queries to Google's embedding API. Check applicable provider terms, privacy requirements, rate quotas, and costs before indexing a large corpus or accepting sensitive queries.

## Load-test staging

Install k6, deploy a stable staging backend with representative Qdrant data, then run:

```bash
BASE_URL=https://<staging-api> API_KEY=<staging-key> RATE_LIMIT_REQUESTS=10000 k6 run tests/load/query.js
```

Use a dedicated staging instance and temporarily raise its in-memory rate limit so the shared load-generator IP does not confound capacity results. Run the rate-limit check separately at the configured 30 requests/minute. The script measures end-to-end single-hop and multi-hop latency, HTTP failure rate, and response shape; it does not measure internal vector-search latency or prove three-day availability.
