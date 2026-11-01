# SkillSphere V3 — Milestone 4.3 Audit

**Audit date:** 2026-11-01  
**Verdict:** Partially ready for a controlled hackathon demonstration. The profile, resume, Gemini analysis, and API persistence paths were exercised locally against disposable PostgreSQL. TinyFish Search succeeded live but returned no candidates for the tested query. TinyFish Agent completed two provider runs remotely, but both outlasted the client polling budget; one completed result was recovered, validated, and reconciled into the disposable database. Do not describe opportunity discovery as a reliably completed end-to-end feature yet.

## Scope and preservation

- Worked only in the V3 backend and read-only frontend review/build. Root `main.py`, SkillSphere V2, frontend source, and the pre-existing Milestone 4.1/4.2 work were preserved.
- The configured development database was not migrated or modified. Migration and persistence checks used disposable PostgreSQL 16 at `127.0.0.1:55432`, database `skillsphere_test`.
- Secret values and private resumes were not printed. The resume test was generated locally and used a unique `/tmp` storage directory.

## System inventory

| Area | Implemented behavior | Audit conclusion |
|---|---|---|
| FastAPI foundation | Versioned `/api/v1` router, health/readiness, OpenAPI, CORS, configuration, SQLAlchemy | Core routes and health tests pass. Readiness does a database `SELECT 1`; health is liveness only. |
| Authentication | Supabase JWT HS256 and JWKS RS256/ES256 verification code; development bearer mode | HS256 and development identity paths are tested. JWKS algorithms and live Supabase are not verified. Current env uses development auth. |
| Profiles | User-scoped profile create/update/read | API flow passed against PostgreSQL; unit/API tests pass. |
| Resumes | PDF/DOCX/text parsing, private local/Supabase adapter, metadata list/get/delete | Generated PDF upload, parse, retrieve, ownership denial, and delete passed against PostgreSQL/local storage. Supabase Storage is unavailable in this environment. |
| Career analysis | Google ADK Runner with typed Gemini output; persisted history and user+resume+model+prompt idempotency | One live Gemini 2.5 Flash request returned two career paths and persisted. Repeated POST reused the same record. |
| TinyFish Search | Search adapter, source registry, query construction, candidate validation, observations | Live HTTP 200 in 2.25s, zero results for the tested India AI/ML internship query. Mocked tests pass. |
| TinyFish Agent | Queue/poll SDK adapter, structured schema, URL/evidence checks, cache, execution rows | Provider completed runs, but runtime exceeded the application poll budget. A late result had zero jobs; no real opportunity evidence was available to verify. |
| TinyFish Fetch | URL-safe fetch adapter | Unit/mocked coverage only; no live fetch verified. |
| Opportunity API | Authenticated discovery, run/status/execution/results, shared detail, save/unsave, paging | Endpoints and ownership behavior have unit coverage. Disposable PostgreSQL exposed and then verified the fix for JSON-column pagination. |
| Frontend | React/Vite UI with profile/resume/analysis API calls plus opportunity/demo screens | Typecheck/lint/build pass. Opportunity cards, auth, tracking, and saved state remain demo/local-only; no frontend opportunity API client exists. |

## Audit fixes completed

- Replaced the synchronous long-held TinyFish Agent request with documented queue-and-poll calls. Provider run IDs, elapsed time, and start timestamps are retained in timeout exceptions and failed execution rows.
- Normalized provider enum casing (`Completed`, `Active`, `High`) before schema validation; the live response demonstrated this provider variation.
- Fixed PostgreSQL opportunity pagination. `DISTINCT` over selected JSON columns fails on PostgreSQL; repository queries now group observation IDs in a subquery before loading opportunity rows.
- Corrected initial migration nullability and content-hash index naming; aligned `TinyFishExecution.source_url` index metadata. Fresh migration to `0006` and `alembic check` pass.
- Made local storage root, user directories, and files private (`0700`/`0600`) and tested those modes.
- Restricted the existing backend `.env` file to owner-only mode (`0600`) without changing its contents. Added cleanup for unexpected resume-parser failures after storage upload.
- Added a logging filter that supplies request IDs when service records omit them, avoiding formatter failures.
- Mapped missing provider/storage configuration to safe HTTP errors. `.env.example` documents TinyFish settings; README setup uses `cp -n` to avoid replacing an existing `.env`.
- Updated the development-auth unit test to call the current bearer dependency contract.

## Verification evidence

- Backend: `uv run --project . --extra dev pytest -q` — **50 passed**, 6 deprecation warnings, 0.48s.
- Static: `ruff check app tests migrations` — clean. `python -m compileall -q app migrations tests` — clean.
- Database: PostgreSQL 16 disposable DB migrated from base through `0006_tinyfish_agent_evidence`; `alembic current` at head; `alembic check` — “No new upgrade operations detected.”
- Resume and AI: authenticated profile `200`; generated PDF upload `201`, parsed; same-user retrieval `200`; other-user resume retrieval `404`; Gemini career-analysis `201` with two paths; repeat reused analysis ID; history returned one row; deletion `204`, subsequent get `404`.
- TinyFish Search: live Search API `200`, 2.25s, 0 candidates. An authenticated API discovery run was persisted, reached `completed`, and results were retrievable (`200`, total 0).
- TinyFish Agent run `c07ea8bb-3a5a-4b73-9670-39aa36b75f04`: `jobs.lever.co/linear`, provider `COMPLETED` at 10:07:43 UTC, 43s after provider start; the local adapter had timed out. Provider redirected to `linear.app/careers`, outside the Lever host, and reported no entry-level/internship matches. Result contained 0 jobs.
- TinyFish Agent run `48c6c0be-12f4-484a-9db7-73b03b717536`: one-company test through `DiscoveryService` with an explicitly seeded search candidate at `jobs.lever.co/anthropic`; provider `COMPLETED` at 10:15:42 UTC, 130s after start. The application’s 120s polling window expired, storing timeout plus provider ID. A later read-only provider lookup returned a schema-valid result with 0 jobs and 2 Agent-reported errors. That same result was reconciled into the disposable DB; authenticated run, execution, and results reads returned `200`; another user’s run read returned `404`. The candidate input was seeded, so this is not a live Search-to-Agent run.
- Gemini: one live Google API request completed in 12.2s through the ADK runner. Provider usage/credits were not exposed in the response and are not claimed.
- Frontend: `npm ci`, `npm run typecheck`, `npm run lint`, and `npm run build` passed. Production dependency audit: 0 findings; full dependency audit: 11 moderate findings in development tooling. No frontend source/lockfile change was made.

## Important remaining issues

1. Agent jobs frequently outlive the configured application polling period. Provider work continues after the application records timeout; there is no automatic late-result reconciliation endpoint/worker. The audit reconciled one provider result manually, using its existing run ID.
2. No live eligible jobs or evidence were returned in the verified Agent runs. Consequently, live evidence persistence, application URL support, and verified listing promotion remain unproven.
3. TinyFish API responses expose no credit usage in the inspected SDK response; usage is unknown.
4. Supabase Auth/Storage were not exercised. Service key is absent and runtime auth/storage mode is development/local.
5. Opportunity discovery uses in-process FastAPI `BackgroundTasks`, not a durable queue. A process restart can strand a run.
6. Frontend opportunity discovery and authentication are demo/local-only. No deterministic personalized match score exists.
7. Resume download is not exposed as an API endpoint. Upload reads the multipart body before the service applies its 10 MB check; add request-level upload limits before public deployment.
8. Full frontend audit reports 11 moderate development-tool dependency findings (minimatch-related); production-only audit reports none. Review and update tooling in a separately tested dependency change.

## Final readiness

Suitable for demonstrating profile setup, generated-resume parsing, a live Gemini analysis, and authenticated discovery API state. Opportunity discovery can be demonstrated as a live search attempt and as transparent Agent execution tracking, but not as a repeatably successful live listing/evidence workflow. See [FEATURE_READINESS_MATRIX.md](FEATURE_READINESS_MATRIX.md), [LIVE_INTEGRATION_RESULTS.md](LIVE_INTEGRATION_RESULTS.md), and [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md).
