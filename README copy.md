# SkillSphere V3 — Documentation Pack

This pack is the product and engineering baseline for designing and implementing SkillSphere V3 with Codex, Stitch MCP, Google ADK, Gemini, and TinyFish.

## Document index

| Document | Purpose |
|---|---|
| `01-product-requirements.md` | Product vision, users, scope, features, requirements, success criteria |
| `02-ui-ux-design-specification.md` | Black-and-orange design system, information architecture, screen specifications, responsive behavior |
| `03-system-architecture.md` | Application architecture, service boundaries, data flow, deployment principles |
| `04-adk-agent-architecture.md` | Google ADK orchestration, specialist agents, tools, workflows, guardrails |
| `05-data-model.md` | Core entities, relationships, persistence and retrieval principles |
| `06-api-contracts.md` | Frontend-facing API conventions and proposed endpoint contracts |
| `07-security-privacy.md` | Authentication, authorization, secrets, prompt-injection defense, privacy |
| `08-testing-quality-plan.md` | Test strategy, acceptance criteria, release gates |
| `09-implementation-roadmap.md` | Phased implementation plan and Codex execution instructions |
| `10-decisions-and-assumptions.md` | Architectural decisions, assumptions to verify, open questions |

## How Codex should use this pack

1. Read all documents before changing code.
2. Inspect the existing repository and report the actual stack, routes, data model, API contracts, and existing functionality.
3. Treat these documents as target requirements, not evidence that a capability already exists.
4. Reconcile proposed APIs and schema with the current repository. Do not blindly overwrite working code.
5. Preserve V2. Build V3 on a separate branch or isolated app path.
6. Use Stitch MCP for actual design creation where supported. Verify the available tools and operations first.
7. Implement in phases and run tests after each phase.
8. Record deviations and unresolved dependencies in `docs/implementation-status.md`.

## Important distinction

The API paths, database entities, and agent topology in this pack are proposed contracts. Codex must validate them against the repository and current official documentation before implementation. Do not invent successful integrations, live opportunity data, or completed external actions.

## Suggested repository placement

Copy this folder into the project as:

```text
docs/skillsphere-v3/
```

Then give Codex the instruction:

> Read every file in `docs/skillsphere-v3/`. Audit the repository and reconcile the documents with the actual implementation. Do not start a broad rewrite. Produce a gap report and phased plan first.
