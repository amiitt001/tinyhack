# Live Integration Results

**Date:** 2026-11-01. No API key or secret values are included below.

## Emergency live verification (2026-11-01, UTC)

### Live Search

- Exact query: `Software engineering internship India 2026 official company careers`.
- Search adapter arguments: location `IN`, page `0`, source `official_company_careers`; include domains `careers.google.com`, `jobs.lever.co`, `boards.greenhouse.io`, `apply.workable.com`, `jobs.ashbyhq.com`, `smartrecruiters.com`, `myworkdayjobs.com`, `taleo.net`.
- HTTP `200 OK`, 1.826 seconds, `total_results=10`, 10 result objects. This was a non-empty Search success; results remain unverified until Agent inspection.
- URLs returned:
  1. `https://jobs.ashbyhq.com/cohere/8c035d3d-081d-4c8a-914a-72f4efaad254`
  2. `https://intel.wd1.myworkdayjobs.com/External/page/f7af6f4ab7131001ecc380a588ca0000`
  3. `https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced/job/XMLNAME-2027-Intern---Software-Engineer_R171666`
  4. `https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite`
  5. `https://kaleris.wd501.myworkdayjobs.com/en-US/kaleris_careers/job/Associate-Software-Engineer-Intern_R-100658`
  6. `https://thehartford.wd5.myworkdayjobs.com/en-US/Careers_External/job/Tech---Data-Program-Summer-2027---Software-Engineer-Intern--Hartford-_R2626105-1`
  7. `https://edwards.wd5.myworkdayjobs.com/en-US/EdwardsCareers/job/India-Pune/IT-Internship-Program--January---June-2027-_Req-50762`
  8. `https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/NVIDIA-2027-Internships--Software-Engineering_JR2023495`
  9. `https://iqvia.wd1.myworkdayjobs.com/en-US/IQVIA/job/Intern_R1567860`
  10. `https://intel.wd1.myworkdayjobs.com/en-US/External/job/AI-Software-Engineer-Intern_JR0288261`
- URL 7 was selected because the live title/snippet said Pune IT internship, January–June 2027. Existing domain and candidate validation accepted it as an unverified candidate. Search snippet text did not establish detailed fields.

### Search-result-to-Agent API workflow

- API discovery run `84c3b139-0a12-419a-bb74-993d71125c1b`; development test identity `tf-emergency-verification`; disposable SQLite database under `/tmp`.
- The discovery service replayed the exact URL, title, and snippet captured from the single live Search response. No URL or job facts were invented, and no second Search request was made.
- Agent queue and poll returned HTTP `200`; provider run ID `0ea720fa-a5e5-43f6-a320-36af06338de6`.
- The Agent exceeded the configured 150-second Agent limit plus the adapter’s 30-second polling allowance. Local duration: `180135 ms`; persisted execution status: `failed`, safe error `timeout`; discovery status: `partially_completed`.
- At `2026-11-01 10:36:06 UTC`, SDK `runs.get` showed the provider run still `RUNNING`. A final read at `10:36:52 UTC` returned `COMPLETED`, with two jobs. Provider duration was 241 seconds, beyond the configured 150-second Agent limit plus 30-second application polling allowance.
- The provider returned `execution_status="Completed successfully. Extracted 2 relevant internship/graduate jobs from the Edwards Lifesciences careers site."` despite the enum schema. Pydantic initially rejected it. A narrow validator now accepts a recognized leading enum token only; the focused TinyFish test module passes (6 passed).
- Provider jobs: `Clinical Graduate Program` (Germany-Field) and `Business Operations Governance & Portfolio Management Intern` (Malaysia-Kuala Lumpur BSC). Output included title, location, description, and other field evidence on official Edwards Workday job URLs. Neither role is in the requested India/Pune location. Application URLs lacked matching evidence and were discarded by the application pipeline. Listing status lacked supporting evidence and was stored as `unknown`; both details are `is_verified=false`.
- Persisted detail/evidence URLs and field summaries:
  - `Clinical Graduate Program`, `Germany-Field`: evidence for title, location, posting date, requisition number, description, and eligibility; evidence URL [Edwards Req-51322](https://edwards.wd5.myworkdayjobs.com/en-US/EdwardsCareers/job/Germany-Field/Clinical-Graduate-Program_Req-51322).
  - `Business Operations Governance & Portfolio Management Intern`, `Malaysia-Kuala Lumpur BSC`: persisted evidence for title, location, requisition number, description, education requirements, and internship duration; evidence URL [Edwards Req-50768](https://edwards.wd5.myworkdayjobs.com/en-US/EdwardsCareers/job/Malaysia-Kuala-Lumpur-BSC/Business-Operations-Governance---Portfolio-Management-Intern_Req-50768).
  - Evidence confidence was provider-reported `high`; the application also required the value to appear in the evidence text and all evidence/job URLs to pass allowed-domain URL validation. Unsupported `application_url` values and non-evidenced `listing_status=active` were not persisted.
- Each detail returned six persisted evidence rows. The provider's `job_url` evidence text did not contain the URL value and was rejected by the substring check; the second role's posting-date evidence was not retained by the application validator. No unsupported field was counted as evidence.
- The late result was reprocessed through the existing `DiscoveryService._investigate_candidate` validation/persistence method, using the already-returned provider result and no new Agent call. The original timeout row remains; an `agent_reconciliation` execution records the completed provider result. The run is completed in disposable SQLite.
- Authenticated run, execution, results, and detail GETs returned `200`. Results contained the original unextracted Search candidate plus two `extracted` roles with persisted evidence. This demonstrates provider output validation, evidence filtering, persistence, and API retrieval after manual late-result recovery.
- **Strict outcome: END-TO-END FAIL.** The normal API workflow timed out and required manual result retrieval/reprocessing. The only extracted roles were outside the requested country, their status was not evidence-backed, and neither was marked verified. No automatic recovery exists.

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

**Conclusion:** Previous Agent runs returned schema-valid zero-job results after polling timeouts. This emergency Search-derived Agent run remained `RUNNING` after the configured 180-second application bound. No listing evidence was demonstrated. The integration is **PARTIAL**, not a successful listing-discovery claim.

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
- `python-dotenv` emitted a parse warning for line 3 during settings reads. The TinyFish key was present to Settings and live calls authenticated, but inspect that local line privately; its contents were not read into or printed in the audit.

## Frontend package checks

- `npm ci` succeeded; `npm run typecheck`, `npm run lint`, and `npm run build` succeeded.
- `npm audit --omit=dev`: zero findings. Full audit: 11 moderate development-tool findings in the minimatch dependency chain. No automatic dependency/lockfile changes were applied.
