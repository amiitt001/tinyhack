# SkillSphere V3 UI

A responsive career workspace built with React 19, TypeScript, Vite, Tailwind CSS and Lucide. The UI uses the existing Python backend for profile basics, uploaded resumes, career analysis and Milestone 4 opportunity APIs.

## Run on Linux

From your Tinyhack repository checkout:

~~~sh
cd tinyhack-ui
npm ci
npm run dev
~~~

Open the address printed by Vite, normally http://localhost:5173. To access the UI refinement branch from the repository root, run git fetch origin followed by git switch ui-discovery-refinement.

Vite proxies /api to http://127.0.0.1:8000. To use another backend address:

~~~sh
VITE_BACKEND_URL=http://127.0.0.1:8000 npm run dev
~~~

Start and configure the backend separately using [backend/README.md](../backend/README.md), including its migrations. Preserve existing environment settings and credentials. The existing development token helper requires AUTH_MODE=development; this UI pass does not implement production sign-in or token issuance.

## Where data lives

| Capability | Storage / dependency |
| --- | --- |
| Profile summary, career stage, completion | Existing profile API; additional presentation fields remain local |
| Uploaded resumes and career analysis | Existing backend APIs and configured providers |
| Discovery runs, results, details and saved opportunities | Milestone 4 API and authenticated user identity |
| Applications, roadmap completion, resume text drafts, practice answers, settings | Browser local storage |
| Optional fictional opportunities and demo saves | Separate local demo state |

Discovery is disabled by default in the backend. The UI displays source availability and does not enable providers. The current official-careers adapter covers approved Canonical paths only. See [discovery setup and limitations](../backend/docs/opportunity-discovery.md). A running API does not by itself establish live discovery availability.

Without the backend, local tools and the explicitly labeled demo remain usable; server-dependent features show connection errors.

## Verify

~~~sh
npm run build
npm test
~~~

Build includes TypeScript checking. Playwright uses /usr/bin/chromium; adjust playwright.config.ts for your local browser installation. Tests intercept the API with controlled fixtures and make no live TinyFish calls.

See [design.md](design.md) for the getdesign.md and 21st.dev reference selection, and [the current implementation report](docs/ui-refinement-report.md) for scope and validation.
