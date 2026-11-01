# Live Integration Results

**Date:** 2026-11-01. No API key or secret values are included below.

## TinyFish SDK and timeout finding

The previous adapter used synchronous `agent.run`, holding one HTTP response open for the entire browser task. That operation returned neither a run ID nor a structured result before the SDK read timeout; an HTTP timeout therefore could not distinguish a provider failure from a still-running remote task.

The installed SDK exposes `agent.queue(...)`, `runs.get(run_id)`, and `runs.list(...)`. The adapter now queues and polls, with SDK transport timeout separated from the Agent duration and zero SDK retries. It retains provider run ID and timing metadata on timeout. Live runs showed the remote Agent can continue beyond the app polling budget: this makes run-ID retention essential, but automatic reconciliation is still missing.

Provider result enum strings were capitalized (`Completed`, `Active`, `High`) despite the app’s lowercase enum contract. Pydantic validators now normalize those fields. The live output motivated and verified this fix.

## TinyFish Search

- Authenticated API request on the disposable PostgreSQL database: `POST /api/v1/opportunity-discoveries`, HTTP `202`.
- Query: AI/ML internship, Python, Machine Learning, FastAPI, India; source `official_company_careers`.
- TinyFish Search HTTP `200`, approximately 2.25 seconds, reported `total_results=0` and returned no candidates.
- API run `83e0ce52-aa13-4763-842a-db830581b9a7` later reached `completed`, with zero results; run and empty result page were retrievable over authenticated API.
- No Agent was started for that run because Search returned no candidates.

## TinyFish Agent

### Run `c07ea8bb-3a5a-4b73-9670-39aa36b75f04`

- Target: `https://jobs.lever.co/linear`; task: find up to two current internship/graduate/entry-level roles with evidence.
- Provider created at `2026-11-01T10:06:52Z`; started at `10:07:00Z`; completed at `10:07:43Z` (43 seconds after start).
- The adapter’s 30-second Agent limit plus polling overhead expired before the response was processed locally. A read-only recent-runs lookup recovered the provider ID/status and result; no second call was made for this target.
- Provider reported that the Lever URL returned 404 and navigated to `linear.app/careers`; it found no entry-level/internship roles. Result contained zero jobs. This redirect was outside the configured Lever domain allowlist, so it was not used as an application listing.
- Provider usage/credits: not exposed by the retrieved SDK response.

### Run `48c6c0be-12f4-484a-9db7-73b03b717536`

- Target: `https://jobs.lever.co/anthropic`; one-company/two-job cap; Agent duration configured to 90 seconds.
- Run entered through `DiscoveryService` and disposable PostgreSQL. The candidate was supplied by a seeded search adapter to isolate Agent/result persistence; this is not a live Search-to-Agent journey.
- Provider started at `2026-11-01T10:13:32Z`, completed at `10:15:42Z` (130 seconds). Application polling ended after 120 seconds and persisted a timeout plus the provider ID. A subsequent read-only `runs.get` showed the same run `COMPLETED`, with a structured result.
- Result validated after enum normalization; it contained zero jobs and two Agent-reported errors. No evidence rows or verified listing resulted.
- The actual late provider result was reconciled into that existing disposable DB execution row; run/execution/results API reads returned `200`, and a different user received `404` for the run.
- This reconciliation was performed manually by the audit script. The application does not yet automatically fetch and reconcile a provider run after its local timeout.
- Provider usage/credits: not exposed.

**Conclusion:** TinyFish Agent can execute remotely and return valid structured output, but completed listings/evidence were not demonstrated. A 30/90-second Agent setting did not bound actual observed provider completion (43/130 seconds). The integration is **PARTIAL**, not a successful listing-discovery claim.

## Gemini / Google ADK

- One authenticated career-analysis API request used a generated test resume, not private user data.
- Google Gemini `gemini-2.5-flash` API returned HTTP `200`; API returned `201` in 12.2 seconds with two typed career paths.
- CareerAnalysis and AgentRun were persisted in PostgreSQL. A repeated request returned the same analysis ID; history contained one row, confirming the idempotent hit did not issue another provider request.
- One request only; timeout and retry exhaustion were not live-triggered. No provider token/credit usage was exposed in the app response.

## PostgreSQL / application APIs

- Disposable `postgres:16-alpine`, bound to `127.0.0.1:55432`; database `skillsphere_test`.
- Fresh Alembic upgrade `0001` → `0006_tinyfish_agent_evidence`, current at head; `alembic check`: “No new upgrade operations detected.”
- Profile `PUT 200`; generated text-bearing PDF upload `201`, status parsed; same-user resume get `200`; other-user resume get `404`; delete `204`; subsequent get `404`.
- Search discovery run, status, execution, and results endpoints returned successful authenticated responses. PostgreSQL initially exposed `DISTINCT` over JSON columns in the results query; replacing it with a grouped ID subquery resolved the defect, and reads passed afterward.
- Cross-user discovery run read returned `404`.
- Opportunity saved/unsaved flows are covered by automated SQLite tests; not repeated against PostgreSQL during this run.

## Supabase

- Configuration presence check found Supabase URL/JWT configuration, but runtime modes were `AUTH_MODE=development`, `STORAGE_BACKEND=local`, and no Supabase service key was configured.
- No live Supabase Auth, JWKS key retrieval, Storage upload, or deletion was attempted. HS256 token verification has offline tests; RS256/ES256 live JWKS is unverified.

## Frontend package checks

- `npm ci` succeeded; `npm run typecheck`, `npm run lint`, and `npm run build` succeeded.
- `npm audit --omit=dev`: zero findings. Full audit: 11 moderate development-tool findings in the minimatch dependency chain. No automatic dependency/lockfile changes were applied.
