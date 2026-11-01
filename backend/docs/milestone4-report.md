# SkillSphere V3 — Milestone 4 implementation report

Implementation date: 1 November 2026. Branch: `milestone4-opportunity-discovery`.
Base inspected: `main` at `aae0a5937d9ae4aab945d55a04e9370f80a2f949`.

## A. Executive summary

Implemented the backend discovery vertical slice: authenticated typed APIs, persistent runs,
classified TinyFish Search integration, policy-constrained detail retrieval, deterministic JSON-LD
extraction/normalization, deduplication, provenance, user-scoped saves, bounded local background
execution, an additive migration, and automated unit/PostgreSQL workflow tests.

**Overall status: foundation implemented and tested; full live milestone acceptance remains
incomplete.** There was no live TinyFish request, source-permission/access verification is not
complete, and the user's Linux PostgreSQL instance on port 5434 is not attached to this environment.
Discovery is disabled by default. A mocked workflow is not presented as a live integration.

The original root `main.py`, frontend `tinyhack-ui/`, historical migration files 0001–0004,
and unrelated existing backend functions were preserved. No user database was reset or accessed.

## B. Architecture

```text
Bearer-authenticated /api/v1 API
  → DiscoveryService (validated request, ownership, idempotency, persistent pending run)
  → bounded process-local executor (atomic pending → running claim)
  → explicit source policy
  → TinyFishAdapter (real AsyncTinyFish Search via worker facade)
  → validated result URL → bounded DNS-pinned HTTPS reader + robots check
  → matching JSON-LD JobPosting evidence → deterministic normalization
  → DiscoveryRepository (aliases, shared listing, separate observation, counters)
  → PostgreSQL transaction → terminal run status
```

Run creation commits before scheduling. Each accepted/rejected observation commits with its
related listing changes and counters. Only successful persistence allows completion. Existing
accepted results survive subsequent provider failure. Matching remains a future integration:
normalized skill, location, experience, employment, work-mode and compensation evidence is kept;
no match scores are generated. The run's authenticated `user_id` links to existing candidate data.

## C. Files changed

All paths below are relative to the repository root.

| File | Purpose / important details |
| --- | --- |
| `.gitignore` | Excludes isolated environments, generated package metadata, caches and task work files. |
| `backend/.env.example` | Adds bounded discovery/retry settings, disabled review/enable flags; no credentials. |
| `backend/README.md` | Entry points for milestone setup, API, contract and this report. |
| `backend/app/api/v1/router.py` | Registers new versioned discovery routes. |
| `backend/app/api/v1/endpoints/discovery.py` | Thin authenticated request/response handlers; explicit saved route ordering and typed errors/source policies. |
| `backend/app/core/config.py` | Bounded provider timeout/attempt and executor/page/result configuration. |
| `backend/app/core/logging.py` | Default request context for safe background logging without formatter failures. |
| `backend/app/integrations/tinyfish.py` | Verified SDK Search contract, async wall-clock cancellation, classified safe errors, bounded retries with jitter/Retry-After. |
| `backend/app/main.py` | Executor lifecycle and domain-error response handler; preserves existing API handlers. |
| `backend/app/models/entities.py` | Nullable additive opportunity fields, exact decimal compensation, canonical/source identity constraints. |
| `backend/app/models/discovery.py` | Persistent runs, observations, saved associations, unique URL/source aliases. |
| `backend/app/models/__init__.py` | Registers new models with existing metadata. |
| `backend/app/discovery/__init__.py` | Discovery package boundary. |
| `backend/app/discovery/errors.py` | Safe HTTP-independent domain errors. |
| `backend/app/discovery/sources.py` | One narrowly scoped implemented source policy and four explicitly unsupported/restricted sources. |
| `backend/app/discovery/security.py` | HTTPS/source/path validation, public DNS pinning, no redirects, robots checks, bounded reads/timer and fail-closed proxy behavior. |
| `backend/app/discovery/extraction.py` | Bounded JSON-LD parser, evidence checks, plain-text normalization, nullable unknowns, deterministic fingerprints. |
| `backend/app/discovery/execution.py` | Worker/queue bounds, capacity errors, shutdown handling; no durable recovery claim. |
| `backend/app/repositories/discovery.py` | Transactions, dedup aliases, public provenance, user-owned runs/saves, pagination and failed-attempt freshness records. |
| `backend/app/schemas/discovery.py` | Typed requests, stable status literals, source/error/detail/page responses. |
| `backend/app/services/discovery.py` | Orchestration, quotas/leases/idempotency, provider invocation and safe partial/failure persistence. |
| `backend/migrations/env.py` | Escapes percent-encoded URLs for Alembic ConfigParser; does not change migration history. |
| `backend/migrations/versions/0005_opportunity_discovery.py` | Additive opportunity columns and four tables; downgrade refuses destructive removal. |
| `backend/tests/discovery/__init__.py` | Prevents nested fixture-module name collisions with legacy tests. |
| `backend/tests/discovery/conftest.py` | Synthetic credentials/content, SQLite and guarded disposable PostgreSQL fixtures, migration preservation sentinel. |
| `backend/tests/discovery/test_adapter.py` | SDK URL contract, response validation, error classification, retry bounds and credential redaction. |
| `backend/tests/discovery/test_validation.py` | Extraction, URL/DNS/redirect/robots/proxy security, injection, nullable unknowns, compensation units. |
| `backend/tests/discovery/test_workflow.py` | API-to-database workflow, isolation, saves, dedup/provenance, rollback, leases and freshness. |
| `backend/tests/discovery/test_execution.py` | Pool capacity, shutdown, real wall-clock cancellation, duplicate claims, partial results, quota, OpenAPI and concurrent PostgreSQL idempotency. |
| `backend/docs/opportunity-discovery.md` | Setup, API examples, configuration, security, migrations and test instructions. |
| `backend/docs/tinyfish-contract.md` | Official references, installed-SDK verification, discrepancies and live-test status. |
| `backend/docs/milestone4-report.md` | This implementation report. |

No production dependency was replaced or downgraded. Disposable PostgreSQL tooling was installed
only in an ignored task environment, not added to the application manifest.

## D. Database

Extended the existing `Opportunity` in place, keeping `source_url`, `verified_at`, IDs, foreign keys,
relationships and records. Added fields include description, location, work mode, employment,
experience, skill arrays, exact compensation and its unit, application/canonical URLs, source
external ID, deadline/expiration, verification/attempt timestamps, extraction state, hash and fingerprint.
Unknown old-row values remain null.

New tables:

- `opportunity_discovery_runs`: user/key uniqueness, request hash, filters, counts, attempts, states,
  timestamps and safe error fields; status and count checks plus user/status-expiration indexes.
- `opportunity_source_observations`: separate accepted/rejected observations, source/run/listing FKs,
  original/canonical URLs, optional request ID, hash-only payload representation and rejection code.
- `opportunity_identities`: database-unique URL and source/external-ID aliases; indexes support
  stable dedup after URL changes without losing observations.
- `saved_opportunities`: composite user/listing primary key and foreign keys; shared data is separate.

**Migration test: PASS.** Fresh disposable PostgreSQL upgraded through historical 0004; a legacy
listing was inserted; 0005 upgraded successfully; the legacy row and its identifier survived.
Tables, indexes, status checks, foreign-key enforcement, rollback and uniqueness were exercised.
No historical revision was edited. Actual local `skillsphere` database upgrade: **BLOCKED**, since
`/home/orion/...` and localhost:5434 refer to the user's unattached Linux machine.

## E. TinyFish integration

SDK pinned by the existing manifest: **0.11.0**. Installed implementation and official documentation
agree on default Search `GET https://api.search.tinyfish.ai/` and `X-API-Key`. Supplying a custom
SDK base changes Search to `/v1/search`; every nonempty application override is rejected safely.

City text is included in the query, not sent as a provider country code. Only the registry's fixed
Search domain is permitted. Responses use the SDK's typed schema and application size/count checks.
The adapter defaults to a ten-second wall-clock attempt limit and three attempts, disables SDK
retries, adds jitter, respects Retry-After when possible, and does not retry credentials or malformed
requests. Provider exception text/bodies/headers are neither persisted nor publicly chained.

**Live provider status: NOT TESTED.** No real request was made, and no production credentials were
used by tests. See [contract verification](tinyfish-contract.md) for exact caveats and references.

## F. Opportunity workflow

Example request body (illustrative contract, not a claim that matching openings exist):

```json
{"query":"Python Developer Intern","location":"Delhi NCR","employment_type":"internship","experience_level":"fresher","skills":["Python","SQL","FastAPI"],"sources":["official_company_careers"]}
```

POST also requires a bearer token and `Idempotency-Key`. A successful accepted request returns
HTTP 202 with the typed run, including its UUID and current status. GET results return a page like:

```json
{"items":[],"total":0,"limit":20,"offset":0,"has_more":false}
```

This is a response-shape example, not a recorded live provider result. In controlled workflow tests,
the pipeline accepted a synthetic structured listing, rejected an unapproved URL before any detail
request, persisted both observations, reported partial completion, returned paginated data, and
allowed only caller-owned saves. The identical key/body scheduled once; conflicting reuse returned
409. Concurrent PostgreSQL creation produced one persistent run.

A valid listing needs matching structured job and application-page evidence, required title/company/
description, approved URLs and valid optional fields. Missing salary, deadline, work-mode or skill
evidence is null. Expired, malformed or unsupported records retain rejection reasons. Compensation
retains the evidence-backed interval rather than assuming monthly/annual equivalence.

Canonical/source-ID aliases and exact business fingerprints normalize duplicates. Distinct IDs from
the same source stay distinct; multiple source observations survive a merge. Failed re-verification
updates `last_attempted_at` without asserting fresh verification or overwriting accepted evidence.

## G. Security

URLs are HTTPS-only, restricted to exact source domains and numeric career-detail paths, with
credential/port/length/query checks. IP literals/local hosts are rejected. Every DNS answer must be
public, and the validated numeric address is pinned for the actual TLS connection. Redirects are
refused altogether. Robots access is checked; unsupported rate/delay guidance fails closed. Existing
required proxies are never bypassed. Source content is bounded to 256 KB and converted to text.

External data cannot change policies, prompts, tools, credentials or destinations: no LLM or agent is
used in extraction and no page instruction is executed. A supplementary instruction-pattern check
rejects obvious injection, but the architectural data-only boundary is the primary protection.

Existing authentication derives identity from verified tokens; no request user ID is accepted.
Runs/results/saves are user-scoped. Shared detail attribution excludes private run/query metadata.
Raw payloads are hashes only, while listing field evidence and safe source URLs are retained.
Database write/lock timeouts, queues, quotas, leases, provider budgets and field limits bound work.

## H. Testing

| Check | Exact result / interpretation |
| --- | --- |
| Existing tests before the dedicated suite | **PASS — 16 passed**, 6 existing deprecation warnings, 0.15 s. |
| Full pytest with disposable PostgreSQL | **PASS — 109 passed**, 16 deprecation warnings, 2.86 s; no skips. Includes 93 new collected cases and 16 original cases. |
| Ruff `ruff check backend` | **PASS — All checks passed.** |
| Discovery mypy | **PASS — no issues in 11 source files**, with `--follow-imports=silent --check-untyped-defs`. |
| Full backend mypy | **FAIL — four pre-existing errors** in unchanged resume/career-analysis ORM-to-response return annotations; documented rather than hidden. |
| Python compilation | **PASS — `python -m compileall -q backend/app backend/migrations`, exit 0.** |
| PostgreSQL migrations | **PASS — historical upgrade, additive 0005 upgrade, legacy-row preservation, schema/index/constraint verification.** |
| API workflow | **PASS — mocked provider through actual service/extraction/repository and PostgreSQL; authenticated status/results/save/pagination/isolation.** |
| Mocked provider tests | **PASS — success, 401, 429, 500, 400, timeout, connection, invalid/missing fields, retry recovery/limit, redaction and installed-SDK endpoint behavior.** |
| Background reliability | **PASS — capacity/shutdown, duplicate claims, hard provider timeout, partial results, rollback/failure, leases and concurrent PostgreSQL idempotency.** |
| OpenAPI | **PASS — typed contracts, pagination and required idempotency header.** |
| Live TinyFish request | **NOT TESTED — no live credential-backed provider call.** |
| Live permitted source verification | **BLOCKED — current access/robots/terms and real extraction are not fully verified; source remains gated.** |
| User's local PostgreSQL on 5434 | **BLOCKED — not attached/reachable from this task environment.** |

The four full-backend type errors are return-value annotations in `endpoints/resumes.py` (two) and
`endpoints/career_analysis.py` (two). Those files were not changed. Ruff and test results do not imply
that these existing annotation issues were fixed.

## I. Remaining limitations

- The Canonical workflow is narrowly implemented and fixture-tested, **not verified live or marked
  permitted by assumption**. Operator review plus a credential-backed smoke test are required
  before enabling it. Other listed sources are explicitly unsupported/restricted.
- The detail transport intentionally refuses required proxies; a reviewed pinning proxy gateway
  is future work. It also rejects redirects, nonmatching JSON-LD, multi-location shapes and any
  unsupported page/application evidence rather than filling gaps with AI-generated values.
- The SDK decodes its response before application field/count checks; transport-level provider
  response byte limiting is not claimed. Source detail pages and persisted representations are bounded.
- Execution is process-local, with no automatic restart replay or durable distributed queue. A DB
  outage may prevent immediate failure persistence; expired lease handling and operator monitoring
  remain necessary. No automatic polling/recovery daemon or public cancel endpoint is claimed.
- The user's existing local database was not migrated here; only fresh task-owned PostgreSQL was.
- Existing full-backend type errors and deprecation warnings remain documented.
- No frontend, full matching engine, auto-application, scraping bypass, new Gemini/ADK execution,
  company-wide source support, production deployment or live opportunity coverage was added.

## J. Next milestone recommendation

First complete controlled activation: review one source's current access terms/robots and real
JSON-LD/application evidence, provide server-side TinyFish configuration, verify permitted network
transport, apply 0005 to the intended local database, and perform a small explicitly permitted live
smoke test with provenance and failure monitoring. Then implement a deterministic matching milestone
using the normalized fields and existing career profile references. Production rollout should also
replace the local pool with an appropriately durable leased worker before promising restart recovery.
