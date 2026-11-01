# SkillSphere


## From “What should I do next?” to a career plan you can act on

Students and early-career professionals do not lack advice. They lack a
trusted system that connects their real experience to the right opportunities,
the skills they are missing, and the next concrete action.

**SkillSphere is an AI-powered career intelligence workspace that turns a
resume and a career goal into personalized, explainable career direction.**

It brings profile building, resume intelligence, career analysis, opportunity
research, and application momentum into one evidence-aware workflow.

---

## The problem

Today’s career journey is fragmented:

- Resumes live in one tool.
- Job searches happen across many websites.
- Learning plans are generic.
- AI advice is often disconnected from the user’s actual evidence.
- Job listings can be stale, duplicated, or impossible to verify.

The result is decision fatigue, wasted applications, and no clear answer to:

> **“Given what I can prove today, which path should I pursue next?”**

---

## Our solution

SkillSphere creates a living career profile from user-controlled information,
then builds an actionable intelligence loop:

```text
Profile + Resume
      ↓
Structured career evidence
      ↓
Personalized analysis
      ↓
Skill gaps and priorities
      ↓
Sourced opportunity discovery
      ↓
Explainable next actions
```

The product is designed around one principle:

> **AI can accelerate decisions, but every important recommendation must be
> grounded, explainable, and clearly labeled.**

---

## The experience

### 1. Build your career profile

Users define their target role, location, education, experience, skills, and
interests. The profile is persisted to PostgreSQL and scoped to the
authenticated user.

### 2. Upload a resume

Users upload a PDF, receive parsed resume data, review its status, and keep
their documents in private, user-scoped storage.

### 3. Understand your next move

Google ADK and Gemini transform the authorized profile and resume evidence into
structured career paths, strengths, skill gaps, learning priorities, and next
steps.

### 4. Discover opportunities responsibly

TinyFish provides controlled web research and extraction boundaries. SkillSphere
adds source allowlists, URL safety, structured validation, provenance, status
tracking, and duplicate protection instead of treating raw web results as
truth.

### 5. Keep momentum

The workspace is built to grow into a complete career operating system:
learning roadmaps, application tracking, interview practice, company research,
and career monitoring.

---

## Why SkillSphere is different

### Personalized, not generic

Recommendations are based on the user’s own profile and resume evidence rather
than a generic career quiz.

### Explainable, not magical

Career paths include strengths, skill gaps, learning priorities, and concrete
next steps. Missing information is surfaced instead of invented.

### Evidence-aware, not scrape-and-hope

External opportunity data is designed to carry source URLs, timestamps,
verification state, completeness, and extraction evidence.

### Deterministic where it matters

Matching, authorization, deduplication, validation, and persistence belong to
reliable application code—not an LLM guessing its way through business rules.

### Privacy-first by design

Resumes remain private, resources are user-scoped, development authentication
cannot run in production, and secrets never belong in the frontend.

---

## Technology

### Frontend

- React
- TypeScript
- Vite
- Responsive SkillSphere workspace UI
- Typed API client with centralized errors, auth headers, and request timeouts

### Backend

- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL

### Intelligence and integrations

- Google ADK for orchestration
- Gemini for structured career analysis
- TinyFish for controlled web research and extraction
- Local and Supabase storage adapters
- Supabase JWT verification boundary for production authentication

---

## What is already working

The foundation is implemented and verified:

- Authenticated user and profile persistence
- Automatic empty-profile initialization for first-time users
- Private resume upload, parsing, retrieval, and deletion
- Local PostgreSQL migrations through the current schema head
- User-scoped authorization and cleanup
- Structured Gemini/ADK career analysis
- Analysis history and idempotent repeat requests
- TinyFish search and agent integration boundaries
- Opportunity discovery API, source registry, URL safety, extraction
  validation, persistence, pagination, and deduplication foundations
- Backend test suite, linting, and compilation validation
- Frontend profile, resume, and career-analysis API integration

The current verified backend suite contains **52 passing tests**.

---

## The demo story

1. Open a personal career workspace.
2. Set a target role and location.
3. Upload a synthetic or consented resume.
4. Review the parsed resume status.
5. Run personalized career analysis.
6. See recommended paths, strengths, skill gaps, and next actions.
7. Submit a focused opportunity discovery request.
8. Inspect provider status, evidence URLs, missing fields, and source
   attribution.
9. Repeat the analysis and demonstrate idempotent behavior.
10. Switch users and demonstrate that private data is isolated.

**The demo never fabricates a listing or hides a provider timeout.**

---

## Responsible AI and data principles

SkillSphere treats career decisions as consequential:

- User data is never silently overwritten by resume parsing.
- External web content is untrusted data, not instructions.
- Provider failures are reported honestly.
- AI-generated analysis is separated from verified facts.
- Application actions require user control.
- Development auth and local storage are explicitly non-production modes.
- Secrets and service-role credentials stay server-side.

---

## Roadmap

### Now

- Harden live provider reliability and reconciliation.
- Complete production Supabase authentication and storage verification.
- Finish frontend opportunity discovery integration.

### Next

- Explainable profile-to-opportunity matching.
- Saved opportunities and application tracking.
- Source freshness and expiry detection.
- Durable background discovery jobs.

### Then

- Skill-gap learning roadmaps.
- Resume improvement workflows.
- Interview preparation and feedback.
- Company intelligence and career monitoring.

---

## The opportunity

Career software is moving from static documents and generic job boards toward
personalized decision support. SkillSphere sits at the intersection of:

- Career guidance
- Verified user evidence
- Responsible web intelligence
- Explainable AI
- Actionable execution

The winning product will not be the one that produces the most advice.

It will be the one that helps a user make **one better decision today**, then
turns that decision into measurable progress tomorrow.

## SkillSphere

**Know your evidence. Find your direction. Take your next step.**
