# SkillSphere V3 — UI design & implementation report

> Historical report from the initial frontend implementation. Backend integration and the current UI have since changed. Use [design.md](../design.md) and [the current refinement report](ui-refinement-report.md) for current behavior and validation.

## Status and provenance

Implemented on the separate `skillsphere-v3` branch in an initially empty repository. No existing frontend, V2, authentication implementation, backend contract, or working feature was present. The remote advertised no refs during inspection. The chosen stack is React 19, TypeScript, React Router, Vite, Tailwind CSS 4, and Lucide.

**This is an integrated local frontend prototype, not a production-connected career platform.** Stitch tools were not exposed to this session. An MCP initialization request to the configured `https://stitch.googleapis.com/mcp` failed at the environment proxy with HTTP 403 CONNECT denial. No Stitch project, screen collection, exported design, or design asset was created. The domain additions were saved in the environment draft in the earlier setup task; publication and authentication remain outstanding. All implemented layouts were authored in the repository.

## Design philosophy

“Your career, with direction.” The workspace balances information density with a quiet, encouraging voice. Orange directs attention toward the next action; charcoal surfaces create hierarchy without ornamental glow. The dashboard uses a bento composition, with profile readiness and the next action above opportunity and skill intelligence. Empty states are intentional product states, rather than fictional results.

## Design system

| Token | Value | Usage |
|---|---|---|
| Background | `#0B0B0D` | Main canvas |
| Sidebar | `#101012` | Persistent navigation |
| Card | `#171719` | Content surfaces |
| Elevated | `#202023` | Menus and overlays |
| Primary | `#FF6B2C` | Main actions and progress |
| Hover | `#FF854D` | Hover and accent text |
| Text | `#F5F5F5` | Primary content |
| Secondary | `#A1A1AA` | Supporting content |
| Border | `#2A2A2E` | Quiet separation |
| Success | `#35B779` | Confirmed local completion |
| Warning | `#F5B942` | Attention |
| Error | `#EF5350` | Error states |

Inter/Geist system font stack; no remote font dependency. If neither is installed, the system sans-serif is used. Main headings 26–29px, section headings 13–15px, body 12–13px, metadata 9–11px. Dashboard metadata is intentionally compact; a larger-text accessibility pass is recommended before production. Analytics use tabular numerals. Spacing follows a 4px base, with 12–24px gaps and 18–28px card padding. Primary surfaces use 10–14px radii; compact controls use 5–8px radii. Minimal shadows are reserved for overlays.

Shared components include PageHead, Card, Badge, Empty, Integration, Modal, UploadResume, CheckRow, Logo, navigation shell, opportunity cards, status selectors, progress bars, toast announcements, search palette, and confirmation patterns. Semantic native selects provide dropdown behavior. Primary, secondary, danger, disabled, focus, selected, and hover variants share tokens. Processing states use a skeleton pattern and `role=status`; errors use explicit messages and alerts. No artificial network success state is displayed.

## Navigation architecture

- Workspace: Overview, My Career Profile, Career Explorer, Opportunities, Company Intelligence.
- Develop: Skill Gap Analysis, Learning Roadmap, Resume Studio, Interview Lab.
- Execute: Applications, Career Monitor, AI Career Coach.
- System: Notifications via header, Activity & Automation via overview and search, Settings, Help & Support.

The sidebar collapses on desktop; mobile uses an overlay drawer. Global search indexes all modules, with Cmd/Ctrl+K and Escape support. Notification and profile actions are in the header. Unknown routes provide recovery to the overview.

## Screen inventory and behavior

| Screen family | Route | Implemented local behavior / limitation |
|---|---|---|
| Authentication | `/auth/sign-in`, `/auth/sign-up`, `/auth/forgot-password`, `/auth/reset-password`, `/auth/verify-email` | Validated forms, password visibility, loading and explicit unavailable-auth states; no credentials retained or sent |
| Onboarding | `/onboarding` | 11 steps, back, optional skip, save, review/edit, local profile initialization; no AI initialization |
| Command Center | `/` | Readiness visual, opportunity metrics, skill compass, roadmap, activity, coach entry; demo score explicitly illustrative |
| Career Profile | `/profile` | Editable details, education, experience, skills, projects, achievements/certifications text, interests, location, resume selection |
| Career Explorer | `/explorer` | Searchable curated role guides, evidence comparison, role comparison, target selection; no live market demand |
| Opportunities | `/opportunities` | Search, location/type filters, sorting, saving, comparison, explicit empty states; fictional demo content opt-in |
| Opportunity Details | `/opportunities/:id` | Skill evidence comparison, missing information states, save, add as Interested; never externally applies |
| Company Intelligence | `/companies` | Searchable demo company states; all unsupported company facts marked unavailable |
| Skill Gap Analysis | `/skills` | Role/evidence filters, exact self-reported skill comparison, roadmap navigation; no inferred proficiency |
| Learning Roadmap | `/roadmap` | Four curated milestones, 12 tasks, durable completion tracking, effort, external learning resources |
| Resume Studio | `/resume` | Plain-text editor, heading insertion, local draft/library, export TXT, upload selection, analysis-unavailable state |
| Interview Lab | `/interview` | Role/type selection, curated questions, answer validation, static reflection checklist, next question, local history including submitted text |
| Applications | `/applications` | Seven status columns, list view, create/edit/delete, notes, recorded date, follow-up date, status updates; no external submission |
| Career Monitor | `/monitor` | Persisted watchlists and pause preferences; never claims monitoring active or checked |
| AI Coach | `/coach` | Session chat UI, prompts, local profile context, history during session, loading/error, links to tools; no generated advice |
| Activity & Automation | `/activity` | Filterable actual local action timeline; automation explicitly disconnected |
| Notifications | `/notifications` | Read/unread filters, mark all read, honest empty state; no invented alerts |
| Settings | `/settings` | Account/career preferences, notification toggles, privacy/security/integrations status, JSON export, typed destructive confirmation |
| Help & Support | `/help` | Context links, expandable FAQ and integration/storage explanations |

## Responsive behavior

Wide desktops use a persistent sidebar and asymmetric two-column dashboard, four metric cards, and three-column discovery cards. At 1200px, space and secondary columns adapt; at 1000px dashboard and details stack. At 760px, mobile navigation replaces the sidebar, metrics become two columns, content cards stack, forms become single column, and resume panels become sequential. Tables and Kanban retain contained horizontal scroll rather than forcing page overflow. Authentication has an intentionally distinct single-column mobile composition. At 390px all route layouts were checked for page overflow. Reduced-motion preferences disable animation.

## User journeys

A. Local onboarding → manual profile review → dashboard. Real signup, resume extraction, and career analysis are blocked on services.

B. Opt into demo → filter opportunities → details → inspect self-reported skill match → save → add to tracker. This is a demonstrated local journey; samples are not real openings.

C. Dashboard → skill checklist → curated roadmap → mark task complete → manually update profile evidence. Completion never automatically asserts proficiency.

D. Resume Studio → select upload (parser unavailable) or manually edit → save → export text. ATS analysis, optimization, document parsing, and PDF export remain service dependencies.

E. Interview Lab → choose role/type → answer curated question → save → static self-review → history. No AI evaluation is represented as completed.

F. Applications → add role → update status → notes/follow-up date → list/board. Reminder delivery is not connected.

## Data contracts and integration gaps

`src/lib/store.tsx` defines typed **local frontend models**, not invented backend contracts: Profile, Application, Notice, and workspace state. No HTTP API routes are guessed. Replace the local adapter with authenticated, validated server contracts only when those contracts are supplied.

Required backend work: authentication and account recovery/verification; profile persistence and document storage; resume parsing with evidence and corrections; sourced opportunity ingestion, deadlines, eligibility, salary and verification timestamps; company research provenance; AI skill recommendations and grounded coach responses; resume analysis with explainable criteria; interview evaluation; background monitoring and notification delivery. Application submission requires an explicit external approval flow if ever added.

The current role checklist checks exact comma-separated names. It is a transparent starter utility, not a semantic inference engine. Readiness is profile-field completion by default; sample scores only appear in labeled demo mode. Missing metrics show an em dash rather than zero. Demo companies, roles, compensation, and counts are illustrative only. There are no outbound application requests.

## Storage and security

Local storage holds profile, progress, watchlists, preferences, applications, activity, resume text, and practice history. It is not encrypted, synced, or suitable for sensitive data on shared devices. Uploaded files are validated for extension/size and selected only; no document contents are parsed or retained. Password fields are never persisted or sent. JSON workspace export covers the central store; resume text has separate TXT export. Data deletion removes all SkillSphere-prefixed local records after explicit typed confirmation.

## Validation and limitations

Build: `npm run build`. Lint: `npm run lint`. Type checking: `npm run typecheck`. Browser tests: `npm test`, using system Chromium. Tests cover every route and document width, navigation/search, durable profile and milestone edits, opportunity filtering/saving/tracking/status update, resume draft, interview reflection, and onboarding at desktop and mobile sizes. Screenshots are generated in ignored `test-results/`.

Known limitations: no Stitch deliverables, backend, secure authentication, document extraction, live AI, real opportunities, company intelligence, background jobs, server deployment, or cloud sync. Notification lists have no upstream producer. Resume sections are plain text rather than structured rich text. Career stage selection is reflected in the onboarding activity record rather than a separately editable profile field. Role guides are curated starting points; the default roadmap is frontend-oriented and says so. No external integrations are claimed to work. Keyboard/focus affordances and a modal focus trap are present, but a full assistive-technology and automated contrast audit remains required before production. Tablet layouts are responsive CSS; dedicated tablet browser coverage is included in the test configuration when available.
