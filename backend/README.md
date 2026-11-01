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
cp .env.example .env
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

## Tests and checks

```bash
pytest
ruff check .
```

The test suite uses an isolated SQLite test double, signed test JWTs, fake storage, and
controlled DOCX fixtures. Live ADK/Gemini calls require credentials. Local PostgreSQL migration
and end-to-end acceptance require a running local PostgreSQL service.

## Milestone 4 — Opportunity discovery

The additive discovery foundation provides authenticated run/status/results, validated shared
listing details, and user-scoped saved opportunities. It is disabled by default pending TinyFish
configuration, current source-access review, and suitable deployment networking. It does not
change the frontend or the original root TinyFish demo.

See [API, setup, source policies, migrations and tests](docs/opportunity-discovery.md),
[verified SDK contract and live-status limitations](docs/tinyfish-contract.md), and
[implementation report](docs/milestone4-report.md).
