# SkillSphere V3 — UI implementation

Updated 1 November 2026 in the Tinyhack project.

## Product context

SkillSphere is a career workspace for students, graduates, and early-career professionals. Its modules cover career profiles, exploration, opportunities, skill development, resumes, interviews, applications, and coaching. The original project specification requires charcoal surfaces and orange accents. That concrete requirement supersedes the earlier generic warm-neutral/blue landing-page assumption in `/workspace/output/design.md`.

## Applied direction

A focused career dashboard with a readable navigation shell, a four-card metric row, an asymmetric profile/next-action composition, opportunity discovery, a skill compass, a learning journey, and actual local activity. Orange identifies actions and the current step. Supporting metric icons use muted purple, green, and blue. Empty states give the user a clear next step.

This implementation is original code informed by public descriptions and usage examples. It does not claim to install or reproduce private component source.

| Reference | Application |
| --- | --- |
| [Header 2 by Efferd](https://21st.dev/@efferd/components/header-2) | Responsive navigation and mobile drawer pattern adapted to the existing app shell. |
| [Hero with image, text and two buttons by Tommy Jepsen](https://21st.dev/@tommyjepsen/components/hero-with-image-text-and-two-buttons) | Clear heading and action hierarchy adapted to a dashboard welcome and next-step card. |
| [Feature Section with Bento Grid by Tommy Jepsen](https://21st.dev/@tommyjepsen/components/feature-section-with-bento-grid) | Asymmetric primary/supporting panel composition. |
| [Button by shadcn](https://21st.dev/@shadcn/components/button/supabase-button) | Consistent primary/secondary controls and visible focus treatment. |

## Tokens and scale

- Canvas: `#0B0B0D`; sidebar: `#101012`; panels: `#161618`.
- Primary: `#FF6B2C`; hover/focus: `#FF854D`.
- Text: `#F5F5F5`; supporting text uses neutral gray.
- Borders: `#2B2B30`; input boundaries: `#4A4A53`.
- Font: Inter/Geist/system sans. No remote font dependency.
- Dashboard heading: 25–35px; section headings: 14–16px; body: 12–14px.
- Primary controls: at least 42px; inputs: at least 44px; card radii: 11–13px.
- Dashboard gaps: 18–23px; card padding: 21–24px.

## Data behavior

Dashboard metrics derive from actual local workspace data: active applications, saved opportunities, completed roadmap tasks, and upcoming recorded follow-ups. Profile progress counts populated profile fields. It is not an AI readiness assessment. The next action responds to the selected target role and the first unfinished roadmap task.

Fictional opportunity listings remain opt-in and labeled. AI, authentication, opportunity ingestion, and other remote services remain disconnected. Existing local profile editing, tracking, roadmap completion, resume drafting, interview practice, and settings remain available.

## Responsive and keyboard behavior

Desktop uses a persistent collapsible sidebar. Below 1050px, dashboard sections stack and the metric row uses two columns. At 760px and below, the sidebar becomes a drawer; the learning journey uses two columns. At very narrow widths, the profile progress visualization stacks above its bars.

The mobile drawer contains Tab focus, closes with Escape, restores focus to its trigger, locks background scrolling, and makes the background inert. Closed mobile navigation is inert. Search retains the existing command shortcut. Reduced-motion preferences disable transitions and animations.

## Files and validation

- `src/pages/Overview.tsx`: redesigned dashboard and derived metrics.
- `src/components/Layout.tsx`: navigation, brand mark, route-aware breadcrumbs, drawer focus behavior.
- `src/refinements.css`: shared UI and responsive dashboard refinements.
- `src/main.tsx`: integrates the shared refinement stylesheet.
- `tests/workspace.spec.ts`: existing journeys plus dashboard data and drawer keyboard checks.

Build with `npm run build`. Run the app with `npm run dev`. Browser journeys run with `npm test`; the configured browser is `/usr/bin/chromium`. This remains a local frontend prototype, with no hosting or backend integration added by this UI pass.
