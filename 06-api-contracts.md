# 6. API Contracts

## 6.1 Contract status

The paths below are proposed REST contracts for planning. They are not claims that these endpoints exist. Codex must inspect the current API and either adopt, adapt, or document the existing routes.

## 6.2 Conventions

- JSON request/response unless file upload is required.
- Authenticated endpoints derive the user identity from the verified session/token.
- Never trust a client-provided `userId` for authorization.
- Use consistent error envelopes.
- Validate request bodies and query parameters.
- Add pagination to list endpoints.
- Use idempotency keys for operations that may be retried.
- Include request/correlation IDs.
- Return ISO 8601 timestamps in UTC.

### Success envelope

```json
{
  "data": {},
  "meta": {
    "requestId": "server-generated-id"
  }
}
```

### Error envelope

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request could not be processed.",
    "details": [],
    "requestId": "server-generated-id"
  }
}
```

Do not expose stack traces, secrets, or internal provider payloads.

## 6.3 Proposed endpoint groups

### Auth and profile
- `GET /api/v1/me`
- `GET /api/v1/profile`
- `PATCH /api/v1/profile`
- `GET /api/v1/profile/completeness`
- `POST /api/v1/profile/skills`
- `PATCH /api/v1/profile/preferences`

### Documents and resumes
- `POST /api/v1/documents`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{documentId}`
- `POST /api/v1/resumes/{resumeId}/parse`
- `GET /api/v1/resumes/{resumeId}/parse-status`
- `GET /api/v1/resumes/{resumeId}/parsed-profile`
- `PATCH /api/v1/resumes/{resumeId}/parsed-profile`
- `POST /api/v1/resumes/{resumeId}/analyze`

### Career intelligence
- `POST /api/v1/career/analyses`
- `GET /api/v1/career/analyses`
- `GET /api/v1/career/roles`
- `GET /api/v1/career/roles/{roleId}`
- `POST /api/v1/career/compare`

### Opportunities
- `GET /api/v1/opportunities`
- `GET /api/v1/opportunities/{opportunityId}`
- `POST /api/v1/opportunities/{opportunityId}/save`
- `DELETE /api/v1/opportunities/{opportunityId}/save`
- `POST /api/v1/opportunities/{opportunityId}/match-analysis`

### Companies
- `GET /api/v1/companies`
- `GET /api/v1/companies/{companyId}`
- `POST /api/v1/companies/{companyId}/research`

### Skills and learning
- `POST /api/v1/skills/gap-analysis`
- `GET /api/v1/skills/gap-analysis`
- `POST /api/v1/learning/roadmaps`
- `GET /api/v1/learning/roadmaps`
- `PATCH /api/v1/learning/milestones/{milestoneId}`

### Resume and interview
- `POST /api/v1/resumes/{resumeId}/job-analysis`
- `POST /api/v1/interviews/sessions`
- `GET /api/v1/interviews/sessions`
- `POST /api/v1/interviews/sessions/{sessionId}/answers`
- `POST /api/v1/interviews/sessions/{sessionId}/feedback`

### Applications and monitoring
- `GET /api/v1/applications`
- `POST /api/v1/applications`
- `PATCH /api/v1/applications/{applicationId}`
- `GET /api/v1/applications/{applicationId}/events`
- `POST /api/v1/monitoring-rules`
- `GET /api/v1/monitoring-rules`
- `PATCH /api/v1/monitoring-rules/{ruleId}`

### Coach and activity
- `POST /api/v1/coach/messages`
- `GET /api/v1/coach/conversations`
- `GET /api/v1/activity`
- `GET /api/v1/notifications`
- `PATCH /api/v1/notifications/{notificationId}`

## 6.4 Long-running agent workflows

For tasks that may take more than a normal request timeout, prefer an asynchronous job pattern:

1. `POST` creates a job and returns `202 Accepted` with a job ID.
2. `GET /api/v1/jobs/{jobId}` returns status and safe progress.
3. A result endpoint or event stream returns the validated result when complete.

Possible statuses: `queued`, `running`, `succeeded`, `partially_succeeded`, `failed`, `cancelled`.

Use server-sent events or WebSockets only if the existing stack and requirements justify them.

## 6.5 API acceptance criteria

- Every endpoint has request and response schemas.
- Every user-owned resource checks ownership.
- Pagination and filtering are consistent.
- Errors are normalized.
- External provider errors are not leaked directly.
- Retry semantics are documented.
- No endpoint claims an external application was submitted without confirmation and provider success.
