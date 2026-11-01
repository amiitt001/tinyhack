# 9. Implementation Roadmap and Codex Instructions

## 9.1 Non-negotiable working rules

- Audit before editing.
- Preserve V2.
- Work on a separate V3 branch or isolated implementation.
- Do not replace the stack without evidence and an explicit decision.
- Do not invent API contracts or provider capabilities.
- Use Stitch MCP only through tools actually available in the session.
- Verify current Google ADK and TinyFish documentation before implementation.
- Never use mock data as if it were live.
- Do not mark work complete without tests.

## 9.2 Phase 0 — Repository audit

Deliver:
- Actual stack and versions.
- Directory map.
- Current routes and components.
- Existing backend APIs.
- Database schema and migrations.
- Authentication design.
- Existing tests.
- Working functionality to preserve.
- Risks and integration gaps.

Stop before major changes and produce a reconciliation report.

## 9.3 Phase 1 — Design system and shell

- Inspect Stitch MCP capabilities.
- Create global design system.
- Generate app shell, sidebar, topbar, dashboard.
- Review desktop/mobile variants.
- Implement design tokens and shared primitives.
- Establish route and layout conventions.

Acceptance: consistent shell, responsive navigation, no regression to existing working routes.

## 9.4 Phase 2 — Core user foundation

- Authentication integration.
- Onboarding.
- Profile management.
- Document upload.
- Resume parse review.
- Dashboard with real profile data.

Acceptance: a user can create and review a complete career profile.

## 9.5 Phase 3 — Opportunity intelligence

- Opportunity search and filters.
- TinyFish adapter after verifying its actual API.
- Normalization and deduplication.
- Source and freshness metadata.
- Opportunity details.
- Deterministic match scoring.
- Save opportunity.

Acceptance: sourced opportunities can be searched, inspected, and saved. No fabricated listings.

## 9.6 Phase 4 — ADK foundation

- Verify ADK version and supported patterns.
- Implement agent gateway.
- Define typed inputs/outputs.
- Implement one vertical slice first: resume/profile-grounded career analysis.
- Add observability, timeouts, permissions, and evaluations.
- Add specialist agents incrementally.

Acceptance: one end-to-end agent workflow is tested and isolated from frontend provider details.

## 9.7 Phase 5 — Career development

- Skill gap analysis.
- Learning roadmap.
- Resume Studio.
- Interview Lab.

Acceptance: each module uses profile/role context and has usable failure/empty states.

## 9.8 Phase 6 — Execution

- Applications tracker.
- Reminders.
- Career monitoring.
- Notifications.
- Company intelligence.
- AI Career Coach expansion.

Acceptance: user can manage the job search without false claims about external actions.

## 9.9 Phase 7 — Hardening and release

- Security review.
- Data isolation tests.
- Agent evaluations.
- Accessibility review.
- Performance and cost review.
- Production configuration.
- Documentation and release checklist.

## 9.10 Recommended Codex operating prompt

Read all files in `docs/skillsphere-v3/` before modifying the repository.

First audit the repository and compare the actual implementation with the documentation. Produce:
1. Existing architecture summary.
2. Feature and route inventory.
3. Reusable code inventory.
4. Gap analysis.
5. Risks and assumptions.
6. Phased implementation plan.

Do not start a destructive rewrite. Preserve V2. Use a separate V3 branch or isolated implementation.

Inspect Stitch MCP tool availability and schemas. Use Stitch to create actual designs where supported. Inspect the installed Google ADK version and current official docs before writing agent code. Verify TinyFish API capabilities before implementing its adapter.

Implement one vertical slice at a time. Keep frontend, backend domain logic, agent orchestration, and external integrations separated. Use deterministic code for CRUD, eligibility, scoring, and state transitions. Use ADK for reasoning and multi-step orchestration where it adds value.

After each phase, run build, lint, type checks, and relevant tests. Update `docs/implementation-status.md` with completed work, evidence, limitations, and next steps. Never claim a design, integration, test, or external action succeeded unless it actually did.
