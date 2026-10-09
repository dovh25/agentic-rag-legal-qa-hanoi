# ADR-0007: Groq as the OpenAI-compatible LLM provider

- **Status**: Accepted for validation
- **Supersedes**: ADR-0006 as the active provider default

## Decision

Use Groq's OpenAI-compatible API for the default synthesis runtime:

- Base URL: `https://api.groq.com/openai/v1`
- Default model: `llama-3.3-70b-versatile`
- Secret: `OPENAI_API_KEY`, injected only through local secret management or Render

The generic `OPENAI_*` names are retained because the application uses the OpenAI
client protocol. `LLM_PROVIDER=groq` makes the deployment intent explicit.

## Safety and rollout

- The API key supplied during chat is intentionally not written to source, `.env.example`,
  documentation, logs, reports, screenshots or commits.
- Set the key in Render's Environment dashboard and in a local untracked `.env` only.
- Revoke/rotate the key because it has been exposed in chat before production use.
- Validate model availability, quota, timeout, fallback and SSE behavior after deployment.
- Provider errors may use the existing deterministic evidence-grounded fallback, but this
  fallback must be reported separately from LLM quality metrics.
