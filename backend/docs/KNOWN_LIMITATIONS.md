# Known Limitations

## TinyFish discovery

- Live Search was available but returned zero results for the tested focused query; no live search-to-agent opportunity was found.
- Provider Agent execution took 43 seconds and 130 seconds in two controlled runs. The application marked one run timed out at its 120-second transport/poll bound while the provider continued; the other smaller-bound task also completed after its poll deadline. Provider run IDs and timeout metadata are retained.
- Late-result recovery is manual. There is no endpoint/worker to inspect outstanding provider runs, reconcile late output, or retry polling after process restart.
- No live Agent result contained jobs/evidence, so positive evidence-to-field matching, application URL support, and verified-listing promotion remain unproven with a real provider result.
- Provider usage/credits were not exposed by SDK responses and cannot be reported.
- TinyFish Fetch was not live-tested. Cache-hit and explicit-refresh behavior were not verified against live provider output.

## Jobs, persistence, and API

- Discovery uses FastAPI `BackgroundTasks`; execution is in-process and non-durable. A process exit can leave a run pending/running without recovery.
- Search can persist unverified candidate observations. `extraction_status=unextracted` must be surfaced honestly until evidence supports detail fields.
- Save/unsave and opportunity ownership have automated fixture tests, but were not re-run on disposable PostgreSQL in this audit.
- No durable queue, provider rate limiter, or per-user run concurrency limit exists beyond adapter-level semaphore constraints.
- Resume download is not exposed by the API. Multipart request size is only rejected after the file is read into application memory; enforce an upstream/request-body limit before public deployment.

## Authentication and storage

- The audit used development bearer identities. Production Supabase Auth and JWKS RS256/ES256 verification were not exercised live.
- Supabase Storage was not tested because no service key was configured. Local storage mode and permissions were verified only on the local filesystem.
- There is no audited deletion/retention policy exercise for hosted storage or all dependent analysis data.

## AI

- One live Gemini/ADK request succeeded; provider timeout, retry exhaustion, and malformed provider output were not live-triggered.
- ADK/Gemini usage quotas and costs were not returned to the application and are not reported.
- Matching is not a deterministic feature. No candidate scoring or ranking engine exists; the frontend’s displayed skill overlap is simple/local comparison.

## Frontend

- Frontend auth is mock/local and creates development tokens. Do not expose it as production authentication.
- Opportunity cards, saved/applied/tracker/preferences state, company research, and background notices remain demo or localStorage state. The UI does not call the backend opportunity endpoints.
- Typecheck, lint, and production build pass, but no browser end-to-end test was run.
- `npm audit --omit=dev` found zero production dependency vulnerabilities; full dependency audit found 11 moderate development-tool findings in the minimatch chain. These were not changed as frontend changes were outside milestone scope.

## Operational / production readiness

- Full backend suite passes, but Starlette reports the current `httpx` TestClient integration as deprecated; FastAPI reports ORJSONResponse deprecation. These warnings did not fail tests.
- Local `.env`/secret filesystem permissions, hosted secret management, production auth, rate limiting, request body limits, durable task recovery, monitoring/alerting, backup/restore, and live load/concurrency behavior were not validated.
- Database migration and model metadata match at `0006`; production data migration/rollback rehearsal was not performed.

These limitations mean this milestone is a controlled demo candidate, not production-ready software.
