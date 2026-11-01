# Hackathon Demo Runbook

## What this build can demonstrate

Reliable demo path: create/update a profile, upload a generated or consented test resume, parse it, run Gemini career analysis, and view persisted analysis history. The opportunity UI is still demo/local state. The backend can show authenticated discovery run/execution/results state and transparent TinyFish outcomes; live Agent jobs/evidence were not returned during this audit.

Suggested framing: **“TinyFish investigates the web. SkillSphere turns the research into personalized career intelligence.”** Explain that this build has verified the research orchestration and persistence boundaries, while live opportunity evidence remains pending a successful listing result.

## Environment setup

1. Use Python 3.12 and Node 20+ (the project pins Python `>=3.12,<3.13`).
2. From `backend/`, create a local `.env` without overwriting an existing file:

   ```bash
   cp -n .env.example .env
   ```

3. Configure a PostgreSQL database, `AUTH_MODE=supabase` and valid Supabase JWT settings for a shared demo, `STORAGE_BACKEND=supabase` plus service key for persistent hosted resume storage, `GEMINI_API_KEY`, and `TINYFISH_API_KEY`. Keep secrets in the environment; do not paste them into a terminal transcript or demo recording.
4. Install backend dependencies and migrate the intended demo database:

   ```bash
   uv sync --extra dev
   uv run alembic upgrade head
   ```

   For an isolated local-only demo, use disposable PostgreSQL and `AUTH_MODE=development`, `STORAGE_BACKEND=local`; the development bearer token is not a public/demo-user authentication system.

5. Start the API:

   ```bash
   uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

6. Frontend, in `tinyhack-ui/`:

   ```bash
   npm ci
   npm run dev
   ```

   Frontend profile/resume/analysis calls can target the API as configured in `src/lib/api.ts`. Opportunity screens currently use demo/local state, not the backend API.

## Demo checklist

- [ ] Confirm `/api/v1/health` and `/api/v1/ready` return healthy responses.
- [ ] Sign in through the configured supported auth flow; the UI’s local `dev:<id>` token is only for development.
- [ ] Create/update profile with a student target and preferred locations.
- [ ] Upload a synthetic or explicitly consented PDF. Avoid using a judge’s/private resume without consent.
- [ ] Confirm parsed metadata and ownership-protected retrieval.
- [ ] Run career analysis once; show the persisted result and history. Repeating the same request should return the existing idempotent analysis.
- [ ] Submit an opportunity discovery request with a focused query and a single official source. The API returns `202` and a run ID.
- [ ] Poll run, executions, and results endpoints. Show actual statuses, provider IDs, evidence URLs, and missing fields if present.
- [ ] Save/unsave only a returned opportunity and show saved pagination; this API is backend-tested, while the UI is not wired to it.
- [ ] Show a second user receives `404` for another user’s discovery run/resume.
- [ ] Clearly label any no-result, timeout, stale, or demo-only state. Never fabricate a job, provider result, source evidence, or live integration.

## Recovery and troubleshooting

| Symptom | Action |
|---|---|
| TinyFish Search returns zero results | Keep the run as a truthful zero-result outcome. Narrow/alter query or location manually and start a new run; do not imply Agent ran when there was no candidate. |
| Agent execution is timed out | Preserve the provider run ID. Inspect that same ID with the SDK’s read-only `runs.get` / `runs.list` before deciding next steps. Do not blindly resubmit. The app currently lacks automatic late-result reconciliation. |
| Provider auth/rate/balance error | Show the safe application error and switch the demo to the profile/Gemini workflow. Do not expose credentials or claim the provider succeeded. |
| Gemini unavailable | Show the safe API failure; do not substitute generated/static analysis as a live result. |
| PostgreSQL readiness fails | Check the configured database URL and migration head; do not migrate an unknown/shared database as part of a demo. |
| Resume upload fails | Check storage configuration, file size/type, and local storage permissions. Never inspect or display another user’s resume. |
| Frontend opportunity card looks populated | Identify it as local demo data; it is not a persisted TinyFish result. |

## Evidence-backed expected outcome

During Milestone 4.3, TinyFish Search returned zero results for one India AI/ML internship query. Two Agent runs completed remotely after application poll timeouts and returned zero eligible jobs. One Gemini call returned two paths in 12.2 seconds. These are audit observations, not promises about future provider behavior.
