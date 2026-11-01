# Opportunity Discovery API — Milestone 4

This is a backend foundation, with no frontend changes. Search alone does not establish a valid job.
All production discovery, status, results, detail, save, and source endpoints require the existing bearer authentication dependency.

## Setup and configuration

Install the backend's existing pinned Python 3.12 dependencies using `pip install -e '.[dev]'`.
Copy `.env.example` only when `.env` does not already exist; preserve existing secrets and settings.
For the original Linux development setup, the database URL points to PostgreSQL database
`skillsphere` on port **5434**. Configure the actual existing connection in `.env`; this task has
not accessed that machine or database.

Run the additive migration from `backend/`:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Migration `0005_opportunity_discovery` extends opportunities with nullable fields and adds runs,
source observations, dedup identities, and saved associations. It preserves old records and all
historical migrations. Downgrade is deliberately unsupported: it raises rather than dropping data.

`TINYFISH_API_KEY` is server-only. Keep `TINYFISH_BASE_URL` empty: SDK 0.11.0 uses the Search
product host only when no explicit base is configured. Non-empty values cause a safe configuration
error when discovery is requested; there is no silent endpoint substitution.

Discovery defaults to disabled. Before enabling it, an operator must review the current terms and
robots/access policy for the specifically scoped source and verify deployment networking. Then set
both `DISCOVERY_ENABLED=true` and `DISCOVERY_OFFICIAL_SOURCE_REVIEWED=true`. A flag records an
operator decision; it is not evidence that this implementation performed the review or a live test.
The current source is deliberately limited to numeric detail paths under `https://canonical.com/careers/`.
It does not mean every company's career website is supported.

The direct detail fetcher pins a public DNS address while verifying the original TLS hostname. It
refuses configured HTTPS/ALL proxies because a reviewed pinning proxy transport is not implemented.
Do not bypass required network policy to enable it. Every retrieval checks robots.txt, refuses
redirects/non-200 responses and explicit crawl-rate/delay rules, and accepts only bounded HTML.
This cloud environment requires a proxy, so its live detail retrieval is intentionally unavailable.

## Endpoint contracts

| Method and path | Behavior |
| --- | --- |
| `GET /api/v1/opportunity-sources` | Explicit source policies, support flags, and runtime states. |
| `POST /api/v1/opportunity-discoveries` | Required `Idempotency-Key`, validated body, returns HTTP 202 and a persistent run. |
| `GET /api/v1/opportunity-discoveries/{run_id}` | Authenticated user's run and counts, safe failure code, timestamps, attempts. |
| `GET /api/v1/opportunity-discoveries/{run_id}/results` | User-scoped, distinct validated listings with source attribution. |
| `GET /api/v1/opportunities/saved` | Only the caller's saved shared listings. Declared before the UUID route. |
| `GET /api/v1/opportunities/{opportunity_id}` | Validated shared listing and accepted public source observations. |
| `POST /api/v1/opportunities/{opportunity_id}/save` | Idempotent caller-owned association; rejects unknown/unvalidated/expired listings. |
| `DELETE /api/v1/opportunities/{opportunity_id}/save` | Idempotently removes only the caller's association; never deletes a listing. |

Example request (requires reviewed/enabled configuration and actual provider access):

```bash
curl -X POST http://localhost:8000/api/v1/opportunity-discoveries \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H 'Idempotency-Key: milestone4-local-001' \
  -H 'Content-Type: application/json' \
  -d '{"query":"Python Developer Intern","location":"Delhi NCR","employment_type":"internship","experience_level":"fresher","skills":["Python","SQL","FastAPI"],"sources":["official_company_careers"]}'
```

This is an API example, not evidence that suitable openings exist at the configured company.
A 202 response is the complete `DiscoveryResponse` schema: `id`, `user_id`, query/filter fields,
`requested_sources`, status, three result counts, `attempt_count`, timestamps, `error_code`, and
`safe_error_message`. Its initial status is normally `pending`; poll the returned ID.

An empty result page has this shape:

```json
{"items":[],"total":0,"limit":20,"offset":0,"has_more":false}
```

Both listing endpoints accept `limit=1..100` and `offset=0..10000`, with deterministic ordering.
Listing detail contains the normalized opportunity fields and `sources`. It does not disclose other
users' run IDs, search queries, raw payloads, or saved state.

Run states: `pending`, `running`, `completed`, `partially_completed`, `failed`, `cancelled`.
No cancel endpoint is introduced. In this version shutdown cancellation is reported as a failed run
with `executor_shutdown`. A zero-hit search can complete successfully; all-rejected candidates fail
with `no_validated_results`; accepted results plus rejected or provider-failed work are partial.

Reusing a key with identical validated input returns the existing run without scheduling again.
A different body with the same user/key returns 409. Keys are scoped to authenticated identity;
request bodies cannot set a user ID. Unknown or another user's run returns the same 404 response.
Errors use `{"detail":{"code":"...","message":"..."}}`; existing auth strings and FastAPI
validation lists are preserved and documented in OpenAPI.

## Source registry and evidence

| Source | Code support | Default state / limitation |
| --- | --- | --- |
| `official_company_careers` | Search plus strict Canonical JSON-LD detail extractor | Configured; disabled pending review and enable flags. Live compatibility unverified. |
| `linkedin_jobs` | No | Restricted; no login/anti-bot bypass. |
| `internshala` | No | Restricted. |
| `naukri` | No | Restricted. |
| `wellfound` | No | Unavailable; no workflow claimed. |

A supported listing needs a matching JSON-LD `JobPosting`, title, matching hiring organization,
nonempty description, approved detail URL, and explicit direct-apply or known application-form
evidence. Multi-location shapes, unsupported extraction, malformed fields, past deadlines, unknown
domains, generic search pages, or instruction-like content are rejected with persisted reason codes.
Unknown salary/deadline/skills/work mode stay null. Compensation includes its evidence-backed unit;
no numeric matching or suitability score is generated. Plain text is returned, never trusted HTML.

## Reliability and storage

The process-local pool defaults to two workers plus four queued runs. Per-user active runs are
limited to two. A compare-and-set claim prevents duplicate workers. PostgreSQL advisory transaction
locks and unique aliases protect dedup/idempotency across application processes; writes use local
five-second statement/lock timeouts. An accepted listing, its aliases, observation, and run counters
commit together. Earlier accepted work survives later failure.

Provider defaults are ten seconds per attempt, three attempts, exponential jitter, and Retry-After
respect. SDK retries are disabled. The async SDK call is wrapped in a wall-clock timeout behind a
synchronous worker facade. The overall work budget defaults to 120 seconds. Detail fetches have a
wall-clock socket shutdown timer, bounded DNS capacity, size limits, and no redirect following.

Runs remain in PostgreSQL after a restart, but the pool is **not durable**: queued/running work is
not replayed automatically. An expired lease is safely marked failed on status retrieval or when
that user submits another discovery. Submit a new key after an abandoned/failed run. Worker and
queue limits are per process. Database outages can also prevent final failure persistence; operator
monitoring and a future durable lease/queue worker remain necessary for production recovery.

Only hash-based raw-payload representations are stored, not provider bodies or HTML. Original
approved URLs and separate observations are retained. Canonical URL aliases remove only known
tracking parameters, preserve allowed job identity parameters, and persist previous URL/source-ID
identities. Exact business fingerprints support cautious cross-source dedup; different same-source
external IDs remain distinct. Ambiguous multiple matches are not automatically merged.

## Tests

```bash
pytest
ruff check .
mypy app/discovery app/integrations/tinyfish.py app/repositories/discovery.py \
  app/services/discovery.py app/api/v1/endpoints/discovery.py app/schemas/discovery.py \
  --follow-imports=silent --check-untyped-defs
python -m compileall -q app migrations
```

The normal suite uses no live TinyFish credentials and no real provider requests. PostgreSQL cases
are skipped unless `DISCOVERY_TEST_DATABASE_URL` names a **fresh disposable** PostgreSQL database
whose name starts with `skillsphere_m4_test`. The fixture refuses other database names. It upgrades
through 0004, inserts a legacy sentinel, upgrades to 0005, and verifies preservation. Use a newly
created test database for each complete migration run, never the existing `skillsphere` database.
For a local PostgreSQL cluster on port 5434, for example:

```bash
createdb -p 5434 skillsphere_m4_test
DISCOVERY_TEST_DATABASE_URL=postgresql+psycopg://localhost:5434/skillsphere_m4_test pytest
```

Use your normal local authentication configuration; do not embed production credentials in commands
or test fixtures. The completed cloud checks used a separately installed disposable PostgreSQL
server in ignored task storage; no production dependency or PostgreSQL reset was added.

The full backend mypy invocation has four pre-existing ORM/response annotation errors in unchanged
resume and career-analysis routes; the new discovery modules are checked separately. Existing
FastAPI/Starlette deprecation warnings do not imply a dependency upgrade was made.
