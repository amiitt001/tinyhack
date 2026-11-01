# 2. UI/UX Design Specification

## 2.1 Design goal

Create a premium, focused career intelligence workspace. It must not resemble a generic job board or a chatbot wrapper.

Reference quality: Linear, Vercel, Notion, Raycast. Do not copy their branding or layouts.

## 2.2 Visual identity: Black × Orange

| Token | Value |
|---|---|
| `bg-app` | `#0B0B0D` |
| `bg-sidebar` | `#101012` |
| `bg-card` | `#171719` |
| `bg-elevated` | `#202023` |
| `accent-primary` | `#FF6B2C` |
| `accent-hover` | `#FF854D` |
| `text-primary` | `#F5F5F5` |
| `text-secondary` | `#A1A1AA` |
| `border-default` | `#2A2A2E` |
| `status-success` | `#35B779` |
| `status-warning` | `#F5B942` |
| `status-error` | `#EF5350` |

Use dark surfaces for approximately 75% of the interface, neutral content for 15%, and orange accents for approximately 10%. Orange is reserved for primary actions, active states, selected data, and meaningful highlights.

Do not use orange as a full-page background or apply it to every card. Avoid excessive gradients, glow, glassmorphism, and decorative motion.

## 2.3 Typography and shape

- Prefer Geist or Inter, subject to repository compatibility.
- Use a clear type scale and consistent line heights.
- Use tabular numerals for scores, dates, and metrics.
- Card radius: 10–14px.
- Borders should be subtle but visible.
- Shadows should be restrained.
- Use Lucide icons consistently.
- Motion should communicate state changes, not decorate the interface.

## 2.4 Application shell

### Desktop
- Collapsible left sidebar.
- Top header with page title/context, global search, notifications, and profile.
- Main content with a consistent max-width and grid.
- Optional contextual right rail on detail/editor screens.

### Sidebar information architecture
**Workspace**
- Overview
- My Career Profile
- Career Explorer
- Opportunities
- Company Intelligence

**Development**
- Skill Gap Analysis
- Learning Roadmap
- Resume Studio
- Interview Lab

**Execution**
- Applications
- Career Monitor
- AI Career Coach

**System**
- Activity & Automation
- Notifications
- Settings
- Help & Support

### Tablet
- Collapsible sidebar or drawer.
- Adaptive two-column layouts.
- Tables become horizontally scrollable or switch to card/list views.

### Mobile
- Dedicated mobile navigation pattern.
- Single-column content.
- Touch-friendly controls.
- No horizontal overflow.
- Forms, charts, filters, and editors must be intentionally adapted rather than merely scaled down.

## 2.5 Screen inventory

1. Sign in
2. Sign up
3. Forgot/reset password
4. Email verification
5. Onboarding wizard
6. Career Command Center
7. Career Profile
8. Career Explorer
9. Opportunities list
10. Opportunity details
11. Company Intelligence
12. Skill Gap Analysis
13. Learning Roadmap
14. Resume Studio
15. Interview Lab
16. Applications Kanban/list
17. Career Monitor
18. AI Career Coach
19. Activity & Automation
20. Notifications
21. Settings
22. Help & Support

## 2.6 Dashboard layout

Prioritize:
- Personalized greeting and career target.
- Profile completeness.
- Career readiness indicators with clear methodology labels.
- Matching and newly discovered opportunities.
- Skill gaps and next learning actions.
- Roadmap progress.
- Application pipeline summary.
- Recent activity.
- AI Coach entry point.

Use a bento-style grid only where it improves information hierarchy. Do not force every section into a card.

Never display fabricated live metrics. Use skeletons while loading and honest empty states when no data exists.

## 2.7 Reusable component inventory

- AppShell, Sidebar, MobileNav, Topbar, Breadcrumbs.
- Button, IconButton, Input, Textarea, Select, Combobox, Checkbox, Radio, Switch.
- Card, MetricCard, Badge, Tooltip, DropdownMenu, Tabs.
- Dialog, Drawer, Toast, Alert, ConfirmationDialog.
- DataTable, Pagination, FilterBar, SearchBar.
- ProgressBar, ProgressRing, ChartContainer.
- OpportunityCard, CompanySummary, SkillChip, SkillGapRow.
- ResumeSection, ResumePreview, InterviewQuestion, ApplicationBoard.
- Skeleton, EmptyState, ErrorState, RetryPanel.

All components need default, hover, focus, active, disabled, loading, and error states where applicable.

## 2.8 Screen-specific interaction notes

- Onboarding: step progress, save/continue, back, optional skips, validation.
- Profile: review extracted resume data before saving.
- Opportunities: filters must be stateful and reflected in the URL where practical.
- Opportunity details: source, discovered time, verification time, and match explanation.
- Resume Studio: editor changes must be explicit; preserve original upload.
- Applications: Kanban and list view; status changes have confirmation and history.
- Interview Lab: session state, answer capture, retry, and feedback.
- AI Coach: show concise task progress and failures; do not expose raw agent internals.
- Settings: confirm destructive or sensitive changes.

## 2.9 Design with Stitch MCP

Codex must:
1. Inspect the available Stitch MCP tool catalog and schemas.
2. Create a SkillSphere V3 design project if supported.
3. Establish global design guidelines before generating screens.
4. Generate the application shell and dashboard first.
5. Validate the shell and design tokens.
6. Generate remaining screens in related groups, reusing the design system.
7. Generate desktop and mobile variants.
8. Review consistency and fix drift before frontend implementation.
9. Export or reference assets only through supported Stitch operations.
10. Report which designs were actually created.

Do not claim Stitch work was completed if the MCP tool was unavailable.
