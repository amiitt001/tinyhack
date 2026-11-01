# SkillSphere V3 Backend

Backend-only FastAPI foundation for the V3 API. The V2 application is preserved separately at
`/home/orion/SkillSphere`; this directory does not import or modify it.

## Requirements

- Python 3.12
- Local PostgreSQL for development (Supabase PostgreSQL is supported for production)
- Supabase JWT configuration for protected production endpoints

## Setup

```bash
cd backend
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
cp -n .env.example .env
```

For local development, set `DATABASE_URL` to a local PostgreSQL database,
`AUTH_MODE=development`, `STORAGE_BACKEND=local`, and `LOCAL_STORAGE_PATH` to a directory
outside any static/public directory. Development bearer tokens use the form
`Authorization: Bearer dev:<synthetic-user-id>`. This mode is rejected when `APP_ENV=production`.

For production, set `AUTH_MODE=supabase`, `STORAGE_BACKEND=supabase`, Supabase JWT
configuration, and `SUPABASE_SERVICE_KEY` in the server environment. Never commit database
passwords, JWT secrets, service-role keys, provider keys, or uploaded resumes. Supabase Storage
uses a private bucket; no public URLs are generated.

## Migrations and execution

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

The local database must be PostgreSQL; migrations are not replaced with SQLite in the
development runtime. The test suite uses an isolated SQLite test double only for fast unit
tests.

OpenAPI is available at `/docs`; health endpoints are `/api/v1/health` and `/api/v1/ready`.

## Milestone 2 API

Authenticated endpoints:

```text
POST   /api/v1/resumes
GET    /api/v1/resumes
GET    /api/v1/resumes/{resume_id}
DELETE /api/v1/resumes/{resume_id}
POST   /api/v1/career-analysis?resume_id={resume_id}
GET    /api/v1/career-analysis/{analysis_id}
```

Resume uploads accept PDF, DOCX, and plain text up to 10 MB. Files are stored under a
user-scoped random object key and metadata is persisted separately.

## Milestone 4 opportunity discovery API

Authenticated endpoints:

```text
POST   /api/v1/opportunity-discoveries
GET    /api/v1/opportunity-discoveries/{run_id}
GET    /api/v1/opportunity-discoveries/{run_id}/executions
GET    /api/v1/opportunity-discoveries/{run_id}/results?limit=20&offset=0
GET    /api/v1/opportunities/{opportunity_id}
POST   /api/v1/opportunities/{opportunity_id}/save
DELETE /api/v1/opportunities/{opportunity_id}/save
GET    /api/v1/opportunities/saved?limit=20&offset=0
```

Discovery uses TinyFish Search to find candidate links and then invokes TinyFish Agent on
approved public career URLs. The Agent navigates listings and detail pages and returns a
bounded JSON result validated by Pydantic. Search candidates remain `unknown` and
`unextracted`; Agent results are promoted only when the listing and evidence URLs match the
source allowlist. Field values are stored only when verbatim evidence supports them. The
Agent task treats page content as untrusted data and forbids login, CAPTCHA bypass, or
application submission. TinyFish Fetch is available through a separate adapter for known
static pages; it checks both requested and final URLs, and is not redundantly called after
Agent navigation.

`0006_tinyfish_agent_evidence` adds `tinyfish_executions` and `opportunity_evidence`, plus a
refresh flag on discovery runs. Execution records include provider run ID, duration, step
count, status, safe error code, and normalized output. TinyFish Agent responses do not expose
credit consumption in the installed SDK response, so credit usage is not estimated or stored.
The successful Agent result cache defaults to 12 hours; set `refresh: true` on the discovery
request to bypass it. Configurable settings: `TINYFISH_AGENT_ENABLED` (default true),
`TINYFISH_AGENT_MAX_CONCURRENCY` (default 3; capped at 3),
`TINYFISH_AGENT_TIMEOUT_SECONDS` (default 150; capped at 180),
`TINYFISH_MAX_COMPANIES_PER_RUN` (default 10),
`TINYFISH_MAX_JOBS_PER_COMPANY` (default 15), and `TINYFISH_CACHE_TTL_HOURS` (default 12).
The adapter bounds concurrent Agent calls to the configured limit. `TINYFISH_API_KEY` is
required; do not expose it to clients.

Example refresh request:

```json
{
  "query": "Backend Developer Intern",
  "location": "Delhi NCR",
  "employment_type": "internship",
  "skills": ["Python", "FastAPI"],
  "refresh": true
}
```

The execution summary is available at
`GET /api/v1/opportunity-discoveries/{run_id}/executions`. Opportunity responses include
field-level evidence records. TinyFish Search's `location` filter is country-level; known
Indian cities are query terms with country code `IN`. Restricted sources remain unavailable.

FastAPI `BackgroundTasks` are in-process and can be lost if the API process terminates; this
is not durable execution. Per-company failures are recorded while discovery continues. Search
and Agent work share the existing bounded run and source policies.

## Tests and checks

```bash
pytest
ruff check .
```

The test suite uses an isolated SQLite test double, signed test JWTs, fake storage, and
controlled DOCX fixtures. Live ADK/Gemini calls require credentials. Local PostgreSQL migration
and end-to-end acceptance require a running local PostgreSQL service.
