# ADR-0005: Browser-owned chat history and stateless streaming chat

## Context

The deployed MVP currently accepts one legal query at a time. A ChatGPT-style experience
needs multiple turns, but legal conversations can contain sensitive case details and the
demo does not yet have authentication or a server-side retention policy.

## Decision

- The browser owns conversation history in IndexedDB. It stores conversation metadata,
  user/assistant messages and verified citation metadata locally.
- The backend remains stateless. `POST /api/v1/chat/stream` receives only the current
  message and a bounded context selected by the browser (maximum 12 messages and 40,000
  characters in the current contract).
- Browser context may resolve references in follow-up questions, but is never treated as
  legal evidence. Retrieval, synthesis grounding and citation verification use Qdrant
  evidence and official source metadata only.
- Responses use SSE events. A grounded final response is emitted in `message_completed`;
  providers that cannot expose token streaming must not be represented as fabricated tokens.
- `/api/v1/query` remains available for API compatibility and non-chat clients.

## Consequences

Positive:

- No conversation database, retention job or cross-user data boundary is introduced.
- Reloading the same browser preserves local sessions and citations.
- The trust boundary is explicit and easy to explain in the demo.

Trade-offs:

- Sessions do not synchronize across devices or browsers.
- Clearing browser storage loses local history.
- Context size is bounded; older turns require user restatement or future summarization.
- SSE proxy buffering and provider quota/timeout behavior must be monitored in deployment.

## Rejected alternatives

- Server-side conversation persistence: deferred until authentication, retention and deletion
  requirements exist.
- Sending the entire unbounded transcript: rejected to control privacy, payload size and
  prompt-injection exposure.
