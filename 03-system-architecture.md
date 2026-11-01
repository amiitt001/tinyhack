# 3. System Architecture

## 3.1 Architecture goals

- Keep the frontend independent of agent implementation.
- Keep business rules deterministic and testable.
- Use ADK for reasoning and multi-step orchestration, not every backend operation.
- Centralize third-party integrations.
- Preserve data provenance and user control.
- Support incremental migration from existing code.

## 3.2 Logical architecture

```text
Web Client (Next.js / React)
        |
        v
Backend API / BFF
  |       |        |
  |       |        +---- Auth / Authorization
  |       +------------- Domain Services
  +--------------------- Agent Gateway
                              |
                              v
                     Google ADK Runtime
                       |      |      |
                    Gemini  Tools  Specialist agents
                              |
                 +------------+------------+
                 |            |            |
              TinyFish    Resume tools   Retrieval
                 |                         |
                 +------------+------------+
                              |
                         PostgreSQL
                       + pgvector*
```

`pgvector` is optional and should be used only where semantic retrieval adds value. Do not add a vector database simply because the product uses AI.

## 3.3 Recommended service boundaries

### Frontend
- Presentation and interaction.
- Form validation for usability.
- API calls through typed client.
- No provider secrets.
- No direct database access.

### Backend API
- Authentication and authorization.
- Input validation.
- Domain workflows and deterministic calculations.
- Persistence and transaction management.
- Agent invocation and result validation.
- Rate limiting and audit events.

### Agent runtime
- ADK orchestration.
- Specialist agent definitions.
- Tool schemas and permissions.
- Context assembly from authorized data.
- Timeouts, retries, cancellation, and output validation.

### Integration gateway
- TinyFish adapter.
- Gemini/model configuration.
- Other external providers.
- Central secret handling, quotas, logging, and provider error normalization.

### Persistence
- PostgreSQL for relational records.
- Object storage for uploaded documents, subject to the existing infrastructure.
- pgvector for embeddings only if justified.
- Separate audit/event records for important operations.

## 3.4 Request flow

1. User performs an action in the frontend.
2. Frontend calls an authenticated backend endpoint.
3. Backend validates request and user permissions.
4. Backend reads only authorized context.
5. If deterministic, domain service performs the operation directly.
6. If reasoning/orchestration is needed, backend invokes the ADK gateway.
7. Agent tools access approved services through typed interfaces.
8. Backend validates output and persists permitted results.
9. Frontend receives a stable response schema.
10. Activity/audit event is written where appropriate.

## 3.5 Data flow and trust boundaries

- Browser input is untrusted.
- Uploaded files are untrusted.
- External websites and TinyFish results are untrusted.
- LLM output is untrusted until validated.
- Tool execution must be allowlisted and permission-scoped.
- User-specific data must be filtered server-side.
- Never trust a user ID supplied in the request body as authorization.

## 3.6 Integration strategy

### Google ADK
Use the current supported Python or other chosen runtime based on repository constraints and official documentation. Keep ADK behind a backend service boundary.

### Gemini
Use through server-side model configuration. Centralize model IDs, generation settings, safety configuration, and usage telemetry.

### TinyFish
Create one integration gateway/adapter. Verify current official TinyFish API documentation and supported capabilities before coding. Do not assume endpoint names, request formats, or feature availability from prior descriptions.

### PostgreSQL
Use existing ORM and migration system if present. Do not introduce a second ORM without a strong reason.

## 3.7 Deployment principles

- Separate frontend and backend deployment only if justified by the existing system.
- Keep agent runtime private to backend services.
- Use environment-based configuration and managed secrets.
- Configure health checks, timeouts, resource limits, and structured logs.
- Use separate development, staging, and production environments.
- Never commit credentials or production data.

## 3.8 Observability

Track:
- Request ID and correlation ID.
- User ID internally, with privacy controls.
- Agent/workflow name.
- Tool invocation names and duration.
- Provider status and normalized errors.
- Token/usage estimates where available.
- Workflow outcome.
- Retry count and timeout events.

Do not log full resumes, passwords, tokens, or sensitive user content by default.
