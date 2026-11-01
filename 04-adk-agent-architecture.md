# 4. Google ADK Agent Architecture

## 4.1 Purpose

Google ADK provides orchestration for workflows requiring reasoning, delegation, or multiple tools. It is not the application's database layer, authorization system, or replacement for deterministic business logic.

Verify the installed ADK version and official documentation before implementing APIs, classes, session handling, callbacks, or deployment patterns.

## 4.2 Proposed agent topology

```text
SkillSphere Orchestrator
  |
  +-- Career Intelligence Agent
  +-- Resume Intelligence Agent
  +-- Opportunity Discovery Agent
  +-- Company Research Agent
  +-- Skill Gap Analysis Agent
  +-- Learning Roadmap Agent
  +-- Interview Preparation Agent
  +-- Application Assistance Agent
```

Do not instantiate or invoke every agent for every request. Route only to the minimum necessary workflow.

## 4.3 Agent responsibilities

### Orchestrator
- Understand user intent.
- Select an approved workflow.
- Delegate to relevant specialists.
- Combine validated results.
- Return a typed response.
- Avoid direct unrestricted database or browser access.

### Career Intelligence Agent
- Analyze user profile and preferences.
- Explain plausible career paths.
- Compare role requirements.
- Cite profile evidence and market sources where available.
- Distinguish facts from hypotheses.

### Resume Intelligence Agent
- Consume canonical parsed resume data.
- Identify missing, unclear, or weak evidence.
- Suggest improvements.
- Tailor suggestions to a supplied job description.
- Never invent experience, skills, qualifications, or achievements.

### Opportunity Discovery Agent
- Request external discovery through the TinyFish gateway.
- Normalize and deduplicate results.
- Preserve source URLs and timestamps.
- Return incomplete/uncertain fields as unknown.
- Never claim that a listing is open unless verified sufficiently.

### Company Research Agent
- Gather sourced company information.
- Separate source-backed facts from inference.
- Include source and verification timestamps.
- Respect provider and website restrictions.

### Skill Gap Analysis Agent
- Compare user evidence with role requirements.
- Use deterministic comparison where possible.
- Explain uncertain skill-level estimates.
- Recommend prioritized gaps.

### Learning Roadmap Agent
- Convert prioritized gaps into milestones.
- Recommend relevant resources and projects.
- Estimate effort with clear uncertainty.
- Avoid promising employment outcomes.

### Interview Preparation Agent
- Generate role-relevant questions.
- Evaluate submitted answers against explicit criteria.
- Provide actionable feedback.
- Avoid claiming objective certainty about interview performance.

### Application Assistance Agent
- Help organize application information and draft materials.
- Prepare an action plan.
- Do not submit forms, send messages, or alter external accounts without explicit confirmation and an approved execution path.

## 4.4 Tool design

Tools should be narrow, typed, permission-scoped, and auditable. Examples of logical tool contracts:

- `get_authorized_career_profile(user_id)`
- `get_user_resume_summary(user_id, resume_id)`
- `search_opportunities(criteria)`
- `fetch_opportunity_details(source_reference)`
- `research_company(company_reference)`
- `get_role_requirements(role_id)`
- `save_career_analysis(user_id, analysis)`
- `create_learning_roadmap(user_id, roadmap)`
- `record_application_status(user_id, application_id, status)`

These are conceptual contracts, not claims about existing tool names. Implement actual tool signatures only after inspecting the repository and ADK documentation.

Never expose a general-purpose SQL tool or unrestricted browser tool to an agent.

## 4.5 Deterministic versus agentic work

| Operation | Preferred implementation |
|---|---|
| CRUD profile | Backend domain service |
| Eligibility rules | Deterministic code |
| Match score calculation | Deterministic, explainable scoring |
| Resume file parsing | Parser/OCR pipeline, then AI interpretation if needed |
| Explain a match | Gemini/ADK |
| Multi-source company research | ADK + approved TinyFish tools |
| Kanban status update | Backend domain service |
| Interview answer feedback | Gemini/ADK |
| Reminder scheduling | Backend/automation service |
| Select specialist workflow | ADK orchestrator or deterministic router |

## 4.6 Standard workflow contract

Every agent workflow should define:
- Input schema.
- Output schema.
- Required user authorization.
- Allowed tools.
- Timeout.
- Retry policy.
- Maximum steps/tool calls.
- Failure behavior.
- Persistence behavior.
- Audit event.
- Data retention expectations.

## 4.7 Output validation

- Validate structured outputs against schemas.
- Reject unknown enum values and malformed fields.
- Treat model-generated URLs as untrusted.
- Verify source URLs and references.
- Do not accept model claims as proof of external action completion.
- Store provenance and generation metadata where useful.
- Return partial results with explicit warnings where safe.

## 4.8 Failure handling

Handle:
- Model unavailable.
- TinyFish unavailable.
- Rate limit.
- Timeout.
- Invalid structured output.
- Tool permission denial.
- Missing profile context.
- Partial external results.
- User cancellation.

Provide retry only for safe, idempotent operations. Avoid blind retries for actions that can create duplicate external effects.

## 4.9 Agent UX

Show human-readable progress such as:
- Reviewing your profile.
- Comparing role requirements.
- Finding matching opportunities.
- Preparing recommendations.

Do not expose internal prompts, raw chain-of-thought, private tool payloads, credentials, or agent stack traces.

## 4.10 Evaluation

Build test cases for:
- Different profiles produce meaningfully different outputs.
- Missing data is not hallucinated.
- User A cannot access User B's context.
- External prompt injection does not trigger unauthorized tools.
- Agent failures produce recoverable UI states.
- Results cite evidence where required.
- Tool calls stay within permissions and budgets.
