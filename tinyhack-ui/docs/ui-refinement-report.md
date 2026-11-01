# UI refinement implementation

Implemented 1 November 2026 on branch ui-discovery-refinement, based on Milestone 4 commit 460d148. This branch includes that backend prerequisite. This UI pass changes files under tinyhack-ui only; it does not enable discovery, change backend routes or migrate data.

## Result

SkillSphere retains its charcoal/orange identity with consistent controls, a Today panel, mobile bottom navigation, a source-aware opportunity interface, URL state, detail dialogs, three-role comparison and clear draft/practice feedback.

Reference selections and visual rules are in [design.md](../design.md), including getdesign.md’s Linear, Vercel and Raycast references and the selected 21st.dev navigation, bento and button patterns. These informed original implementation; no component package or design CLI was installed.

## Main changes

| Area | Files | Behavior |
| --- | --- | --- |
| Shared system | src/refinements.css; src/components/ui.tsx | Semantic color/control tokens, responsive styles, native modal focus behavior and reduced-motion support |
| Shell | src/components/Layout.tsx | Mobile bottom navigation, More drawer focus restoration, command quick actions and scoped connection status |
| Overview | src/pages/Overview.tsx | Data-derived Today actions and authoritative saved total outside demo mode |
| API adapter | src/lib/api.ts; src/lib/opportunities.ts | Typed Milestone 4 endpoints, structured errors, cancellation and safe display formatting |
| Discovery state | src/hooks/useOpportunityDiscovery.ts | Source loading, bounded polling, paginated reads, idempotent creation retry and acknowledged saves |
| Opportunity screens | src/pages/Opportunities.tsx; src/components/opportunities/OpportunityUI.tsx; src/main.tsx | Search, saved tab, source availability, real run states, cards, detail dialog/direct route, comparison and separate fictional demo |
| Resume / practice | src/pages/Development.tsx | Text preview, saved/unsaved state, question progress and answer-save feedback |
| Profile copy | src/pages/Profile.tsx | Describes the existing profile/resume integration accurately |
| Browser coverage | tests/fixtures.ts; tests/discovery.spec.ts; tests/workspace.spec.ts | Controlled HTTP fixtures plus existing workspace journeys |

## Verification

- npm run build: passes TypeScript checking and production bundling.
- npm test: 41 passed, one skipped (the mobile-only drawer test is intentionally skipped in the desktop project), 1.4 minutes.
- Browser layouts checked at 320, 375, 768, 1024 and 1440px, including mobile preferences and navigation focus.
- Existing profile, roadmap, demo save/compare/track, resume, interview, onboarding, dashboard and navigation journeys remain covered.
- New cases cover unavailable sources, connection recovery, structured failures, expired authentication, creation retry keys, partial/failed runs, stopped polling, pagination, details, saved state across reload, unsave, comparison limits, expired application URLs and resume preview.

Browser tests mock all API responses. Listings are labeled synthetic test fixtures in the test code. They do not demonstrate real openings, current salaries, live TinyFish compatibility, production authentication or a deployed service.

## Reviewed previews

These captures use the same synthetic HTTP fixtures; they illustrate layout and interaction states.

| Screen | Preview |
| --- | --- |
| Overview, desktop | [Open screenshot](previews/overview-desktop.png) |
| Discovery results, desktop | [Open screenshot](previews/discovery-desktop.png) |
| Discovery, mobile | [Open screenshot](previews/discovery-mobile.png) |
| Opportunity details, mobile | [Open screenshot](previews/details-mobile.png) |
| Resume preview, desktop | [Open screenshot](previews/resume-desktop.png) |

## Current limits

Discovery remains disabled by default and subject to the backend’s provider/source review requirements. This UI does not change those settings. Supported source scope is limited to approved Canonical detail paths. No new AI scoring, company research, monitoring or automatic applications are introduced.

Application tracking, roadmap progress, text resume drafts, interview answers and preferences remain on the current browser. Production authentication is outside this change. The API does not provide a per-listing saved flag; the UI initially loads up to 100 saved IDs, also learns IDs while paging the saved list, and refreshes authoritative totals after mutations. Saving an already saved listing remains idempotent.

## Run locally

Follow [the UI README](../README.md). From a repository checkout, enter tinyhack-ui and run npm ci, then npm run dev. Configure and start the existing backend separately. The Vite proxy targets port 8000 by default; no hosting deployment is created by this branch.
