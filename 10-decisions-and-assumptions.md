# 10. Decisions, Assumptions, and Open Questions

## 10.1 Current product decisions

| Area | Direction |
|---|---|
| Product | SkillSphere V3 career intelligence platform |
| Audience | Students, graduates, early-career job seekers |
| Visual identity | Premium black and orange |
| Frontend | Preserve existing stack; likely Next.js/React/TypeScript if confirmed |
| Design tool | Stitch MCP, subject to tool availability |
| Agent orchestration | Google ADK |
| Reasoning model | Gemini, subject to configured model/version |
| Web intelligence | TinyFish, subject to current API verification |
| Persistence | Existing database first; PostgreSQL is the target direction if confirmed |
| Retrieval | pgvector only if a concrete semantic retrieval need is demonstrated |

## 10.2 Architectural decisions

### ADK is not the whole backend
ADK coordinates agentic workflows. Authentication, CRUD, authorization, transactions, deterministic scoring, and application state remain backend responsibilities.

### Frontend does not call agents directly
The frontend uses stable backend APIs. Agent providers remain server-side.

### Match scores are deterministic
The backend calculates scores from documented criteria. Gemini may explain a score but does not invent the numeric result.

### External actions require user control
No job application, message, or account change is submitted without explicit user confirmation and verified execution support.

### Preserve source provenance
External data must retain source and freshness metadata.

### Preserve V2
Do not delete, overwrite, or migrate V2 destructively. Keep V3 isolated.

## 10.3 Assumptions to verify

Codex must inspect the repository and confirm:
- Current frontend framework and version.
- Current backend framework and version.
- Existing auth provider and session model.
- Current ORM and database.
- Current file storage.
- Existing API route conventions.
- Existing design system and component library.
- Existing deployment platform.
- Current Google ADK package/version.
- Current Gemini model access and configuration.
- Current TinyFish API plan, endpoints, and capabilities.
- Whether Stitch MCP is connected and which operations it supports.

## 10.4 Open product questions

Do not block the initial repository audit on these. Record recommendations and ask only when a decision materially affects implementation.

1. Which opportunity sources and regions are launch priorities?
2. Is the first release internship-first, or should full-time roles have equal priority?
3. Which resume export formats are required?
4. Should users be able to connect calendars in the first release?
5. Which notification channels are supported at launch?
6. What is the data retention policy for resumes and conversations?
7. What is the acceptable budget/latency target for agent workflows?
8. Which company research fields are essential for the first release?

## 10.5 Explicit non-goals for initial release

- Fully autonomous job applications.
- Unverified claims about job availability.
- Guaranteed ATS pass or job placement.
- Unrestricted autonomous browser access.
- A separate agent for every small UI action.
- Vector database usage without a retrieval requirement.
- Replacing all existing infrastructure without an audit.
