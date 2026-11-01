# Feature Readiness Matrix

Statuses describe evidence collected on 2026-11-01. `PASS` means implementation and relevant verification were both completed; provider-specific or otherwise incomplete verification is marked `PARTIAL`.

| Feature | Backend | Database | API | External service | Tests | Overall |
|---|---|---|---|---|---|---|
| Startup, configuration, CORS, OpenAPI | PASS | PARTIAL | PASS | N/A | PASS | PASS |
| Health / readiness | PASS | PASS (`SELECT 1`) | PASS | N/A | PASS | PASS |
| SQLAlchemy models / migrations 0001–0006 | PASS | PASS (fresh PostgreSQL 16 upgrade, head, metadata check) | N/A | N/A | PASS | PASS |
| Development bearer identity | PASS | N/A | PASS | N/A | PASS | PASS (development only) |
| Supabase HS256 verification | PASS | N/A | PARTIAL | NOT_TESTED live issuer | PASS mocked token tests | PARTIAL |
| Supabase RS256/ES256 JWKS | PASS implementation | N/A | PARTIAL | NOT_TESTED | NOT_TESTED | PARTIAL |
| Supabase user/storage integration | PASS adapters exist | N/A | PARTIAL | NOT_TESTED; service key absent | Mocked only | PARTIAL |
| User/profile persistence and ownership | PASS | PASS (disposable PostgreSQL) | PASS | N/A | PASS | PASS |
| Resume PDF parsing and local storage | PASS | PASS (metadata) | PASS upload/get/delete | Local only; Supabase NOT_TESTED | Mocked unit + live local API flow | PASS for local development |
| Resume ownership / cleanup | PASS | PASS | PASS (cross-user 404, delete 204 then 404) | Local storage | PASS | PASS for tested path |
| Resume Supabase storage | PASS adapter exists | N/A | PARTIAL | NOT_TESTED | Mocked only | PARTIAL |
| Gemini / ADK career analysis | PASS | PASS (analysis and AgentRun) | PASS | PASS: one live Gemini request | Automated + live API | PASS for one bounded case |
| Analysis history / idempotency | PASS | PASS | PASS | N/A | PASS; second POST reused ID | PASS |
| TinyFish Search adapter | PASS | N/A | PASS via discovery | PARTIAL: live 200, zero results | Mocked + one live call | PARTIAL |
| Source registry / URL filtering | PASS | N/A | PASS | N/A | PASS | PASS for covered domains |
| TinyFish Agent queue/poll adapter | PASS | Partial execution rows | PARTIAL | PARTIAL: two provider runs completed after app poll timeout | Mocked queue/poll/schema/timeout tests | PARTIAL |
| Agent execution ID and late-result handling | PASS stores ID/time | PASS, one late result manually reconciled | PARTIAL | Live provider retrieval passed | Unit and disposable PG | PARTIAL; no automatic reconciliation |
| Agent structured output | PASS; provider enum casing normalized | PASS for reconciled zero-job result | PARTIAL | Live schema validation passed | Mocked + live | PARTIAL; no positive job payload |
| Agent evidence and application URL verification | PASS implementation | NOT_TESTED positive evidence | NOT_TESTED positive evidence | NOT_TESTED; zero jobs | Mocked tests only | PARTIAL |
| Opportunity search observations and dedupe | PASS | PASS for empty and seeded candidate workflows | PASS | PARTIAL | Mocked + PG | PARTIAL |
| Opportunity details/results/pagination | PASS | PASS; PostgreSQL JSON DISTINCT defect fixed | PASS (200 reads) | N/A | Unit + PG API | PASS for empty/seeded rows |
| Opportunity save/unsave and ownership | PASS | PASS in SQLite unit fixture | PASS via endpoint functions | N/A | PASS mocked DB | PARTIAL (not repeated on PostgreSQL) |
| Agent cache / explicit refresh | PASS implementation | PARTIAL | PASS request contract | NOT_TESTED live cache hit/refresh | Unit coverage partial | PARTIAL |
| TinyFish Fetch | PASS adapter | N/A | No user endpoint | NOT_TESTED live | Mocked only | PARTIAL |
| Durable background execution / recovery | NOT_IMPLEMENTED | N/A | In-process BackgroundTasks only | N/A | N/A | NOT_IMPLEMENTED |
| Frontend profile/resume/analysis API use | PASS client code | Backend persistence tested | PARTIAL frontend auth is synthetic dev token | N/A | Typecheck/lint/build pass | PARTIAL |
| Frontend opportunity discovery | NOT_IMPLEMENTED API client | localStorage/demo objects | NOT_IMPLEMENTED | NOT_TESTED | Build passes only | NOT_IMPLEMENTED |
| Personalized matching score | NOT_IMPLEMENTED | NOT_IMPLEMENTED | NOT_IMPLEMENTED | N/A | N/A | NOT_IMPLEMENTED |
| Company research, reminders, background automations | NOT_IMPLEMENTED | local/demo state only | NOT_IMPLEMENTED | NOT_TESTED | Build passes only | NOT_IMPLEMENTED |

## Frontend-to-backend mapping

| Frontend feature | Backend endpoint | Persistence | Verification |
|---|---|---|---|
| Career profile | `GET/PUT /api/v1/career-profile` | PostgreSQL user/profile tables | Live disposable API `PUT 200`; backend tests pass |
| Resume upload/list/detail | `/api/v1/resumes` | PostgreSQL metadata + configured object storage | Generated PDF local storage API upload/get/delete; Supabase not tested |
| Career analysis/history | `POST/GET /api/v1/career-analysis` | PostgreSQL CareerAnalysis and AgentRun | One live Gemini API response and idempotent repeat |
| Sign-in / sign-up | No production auth flow in UI; local `dev:<id>` token | None | Mock/demo only |
| Opportunity cards, filters, saved roles, tracker | No frontend call to `/api/v1/opportunity-discoveries` or saved endpoints | localStorage/demo fixtures | Backend endpoints tested separately; frontend not integrated |
| Company research / notices | No backend endpoint wired from UI | local/demo state | Not integrated |

## Test classification

- **Automated/unit:** adapters, parsing, schema validation, auth, endpoint ownership, idempotency, storage permissions, and opportunity service tests use fixtures/mocks or SQLite.
- **Local integration:** disposable PostgreSQL migrations and authenticated APIs; generated PDF/local storage; profile, analysis, and discovery persistence.
- **Live external:** one TinyFish Search call (zero candidates), two TinyFish Agent runs (completed remotely, zero jobs, polling timeout), and one Gemini/ADK request (two paths). Supabase and TinyFish Fetch were not live-tested.
