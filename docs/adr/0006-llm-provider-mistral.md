# ADR-0006: Mistral as the OpenAI-compatible LLM provider

- **Status**: Superseded by ADR-0007
- **Supersedes**: Gemini default in ADR-0002

## Decision

Use Mistral's OpenAI-compatible API as the default synthesis provider:

- Base URL: `https://api.mistral.ai/v1`
- Default model: `mistral-small-latest`
- Secret: `OPENAI_API_KEY`, injected only through local secret management or Render

The application keeps generic `OPENAI_*` names because the Python client uses the
OpenAI-compatible protocol. `LLM_PROVIDER=mistral` makes deployment intent explicit.

## Safety and rollback

- No real key is stored in `.env.example`, source, tests, documentation, logs or commits.
- Provider errors fall back only to deterministic evidence-grounded synthesis; they must not
  create unsupported citations.
- A different OpenAI-compatible provider can be restored by changing provider, base URL and
  model together, followed by the same smoke/evaluation gate.
- A key exposed outside an approved secret store must be revoked and rotated before use.
