# SkillSphere V3 — UI design system

Updated 1 November 2026. Implemented in the existing Tinyhack React application.

## Direction

A calm career workspace that turns a large goal into a useful next step. Preserve the charcoal canvas and orange actions. Use spacing, surface depth, typography and clear source information to establish hierarchy. Reserve motion for processing and simple state transitions.

This pass connects the opportunity interface to the existing Milestone 4 API. Availability is determined by the backend; empty states remain useful when discovery is disabled.

## Selected references

These references inform original implementation choices; no third-party component source or design CLI was installed.

| Reference | Applied element |
| --- | --- |
| [getdesign.md — Linear](https://getdesign.md/design-md/linear.app/preview) | Quiet dark surfaces, restrained accents, dense navigation and clear panel boundaries. |
| [getdesign.md — Vercel](https://getdesign.md/vercel/design-md) | Heading hierarchy, neutral typography, subtle borders and predictable spacing. |
| [getdesign.md — Raycast](https://getdesign.md/raycast/design-md) | Compact controls, keyboard access, command search and quick actions. |
| [21st.dev — Efferd Header 2](https://21st.dev/@efferd/components/header-2) | Responsive navigation adapted to the existing workspace shell. |
| [21st.dev — Tommy Jepsen Bento Grid](https://21st.dev/@tommyjepsen/components/feature-section-with-bento-grid) | Asymmetric dashboard composition with a primary action and supporting panels. |
| [21st.dev — shadcn Button](https://21st.dev/@shadcn/components/button/supabase-button) | Consistent primary, secondary, disabled, selected and focus states. |

## Shared tokens

The semantic variables live in src/refinements.css.

| Token | Value | Purpose |
| --- | --- | --- |
| surface-canvas | #0B0B0D | Page background |
| surface-sidebar | #101012 | Navigation |
| surface-panel | #161618 | Main cards |
| surface-raised | #202023 | Elevated controls and menus |
| text-primary | #F5F5F5 | Headings and primary content |
| text-secondary | #B0B0BB | Supporting copy |
| text-muted | #9696A3 | Secondary labels |
| border-subtle | #2C2C32 | Panel separation |
| border-control | #494951 | Input boundaries |
| accent / accent-hover | #FF6B2C / #FF854D | Primary actions and focus |
| radius-control / radius-panel | 8px / 13px | Shared control and card shapes |

Inter/Geist/system sans; no remote font request. Large headings use 29–38px, primary body copy 14px, controls 13–14px and compact metadata 10–12px. Primary and icon buttons use a shared 44px minimum target, with compact secondary treatments where space requires. Text wraps within its panel; long descriptions remain plain text.

## Screen changes

### Opportunities

Discover and Saved are distinct URL-backed tabs. Desktop pairs a search sidebar with a results grid; medium widths use one results column. Mobile stacks the layout and collapses search preferences after creation so results are easier to reach.

The form accepts role, optional location, employment type, experience and comma-separated skills. Only sources reported as supported and enabled can be selected. A source dialog explains current states and actual domain coverage without configuration controls.

Cards show company, role, location, work mode, skills, compensation, source domain and verification date. Missing information is explicit. Compensation retains the API’s currency and pay period. No match score or company logo is invented.

A right-hand detail dialog keeps the result page and filters. On mobile it occupies the full screen. Direct detail URLs remain available. External links accept HTTPS URLs without embedded credentials; expired application links are withheld. Tracking is explicitly local and does not submit an application.

Comparison supports up to three opportunities using their listed fields. Saved opportunities use authenticated API associations. Demo jobs are opt-in, visibly fictional and use separate local saves.

### Overview and navigation

The Today panel uses the next unfinished learning task, recorded follow-ups and incomplete profile sections. Saved totals come from the server outside demo mode; unavailable counts show a dash. The existing dashboard composition remains intact.

Mobile adds Overview, Discover, Roadmap, Applications and More navigation. More opens the existing keyboard-accessible drawer. The command palette retains page search and adds application/resume shortcuts. Connection copy identifies the profile/resume API rather than implying all services are available.

### Resume and interview

Resume Studio switches between editable text and a rendered preview. Saved locally and Unsaved changes describe the actual draft state. Section controls return to the editor. Text export and the existing upload/analysis integration remain available.

Interview practice shows the current question, session progress and answer-save acknowledgment. Reflection remains a static self-review; the interface does not claim an AI evaluation.

## State and interaction rules

- Source loading, disabled sources, service failure and expired authentication have distinct copy and recovery actions.
- A creation retry after an uncertain response retains its idempotency key for the same input. Duplicate clicks are guarded.
- Poll only pending/running discoveries; pause in hidden tabs, stop on terminal states and bound automatic polling to five minutes. Status retry reads the existing run.
- Show actual run stages and accepted/rejected/reviewed counts. Partial results remain usable. Failure and unavailable status do not display completed stages.
- Pagination, the selected tab and open detail ID survive refresh through URL parameters. Closing details preserves the result page.
- Save state changes after acknowledgment. A failed mutation reports the error and leaves the previous state intact.
- Abort superseded reads and stop polling on unmount. Refresh failures preserve displayed results.

## Accessibility and responsive behavior

Native modal dialogs provide background inertness and focus containment; Escape closes them and focus returns to the triggering element. Labels, pressed/selected states, error alerts and polite status updates explain control state. The mobile drawer also restores the actual trigger, including More.

The header truncates long route labels and removes redundant breadcrumb text on narrow screens. Discovery is checked at 320, 375, 768, 1024 and 1440px without page overflow. Reduced-motion preferences disable the new spinner and shimmer animations. Browser verification is not a full accessibility conformance audit.

## Implementation and verification

See [the current implementation report](docs/ui-refinement-report.md) for changed areas, tests, setup and remaining limits. The earlier UI report is retained as historical context.

Run npm run build for TypeScript and production bundling, and npm test for desktop/mobile browser journeys. Browser API responses in tests are controlled fixtures, not live provider results.
