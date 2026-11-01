# 1. Product Requirements Document (PRD)

## 1.1 Product summary

**Name:** SkillSphere V3  
**Category:** AI-powered career intelligence and opportunity execution platform  
**Primary audience:** Students, fresh graduates, internship seekers, job seekers, and early-career professionals.

SkillSphere helps a user understand their career direction, discover relevant opportunities, identify skill gaps, improve application materials, prepare for interviews, and track their job search from one workspace.

## 1.2 Problem statement

Career tools are fragmented. Users often maintain separate tools for resumes, job discovery, learning, interview practice, and application tracking. Generic AI advice is frequently insufficiently grounded in the user's actual profile and target role.

SkillSphere should provide a coherent workflow grounded in the user's verified profile and sourced opportunity data.

## 1.3 Product principles

1. Personalization must be based on user-specific evidence, not generic templates.
2. Recommendations must explain why they were made.
3. External opportunity and company claims must have sources and freshness metadata.
4. Deterministic business rules must not be delegated to an LLM.
5. Users retain control over applications and consequential actions.
6. The UI must distinguish verified facts, AI-generated analysis, estimates, and missing data.
7. Build a reliable core before adding autonomous behavior.

## 1.4 User personas

### Student / internship seeker
Needs to identify realistic roles, find internships, understand eligibility, build skills, and improve a resume.

### Graduate / entry-level job seeker
Needs targeted job discovery, application management, interview preparation, and feedback.

### Early-career professional
Needs career transition guidance, skill-gap analysis, company research, and a focused learning plan.

## 1.5 Primary user journeys

### A. First-time activation
Sign up → onboarding → resume upload or manual profile → review extracted profile → choose target roles → career analysis → dashboard.

### B. Opportunity discovery
Dashboard → opportunities → filters → opportunity details → eligibility and match explanation → save → user-approved application workflow → tracker.

### C. Career improvement
Career target → skill gap analysis → learning roadmap → complete milestone → update profile evidence → reassess.

### D. Resume improvement
Resume Studio → upload/select resume → review parsed content → select target job → analysis → edit suggestions → preview/export.

### E. Interview preparation
Select target role → choose interview type → practice → submit answer → receive evidence-based feedback → review history.

## 1.6 Product modules and functional requirements

### Authentication and account
- Sign up, sign in, sign out, password reset, email verification.
- Google sign-in only if supported by the existing identity provider.
- Protected routes and session expiry handling.

### Onboarding
- Collect education, experience, skills, interests, target roles, and location preferences.
- Allow resume upload or manual entry.
- Show extracted fields for user review and correction.
- Save progress and allow optional fields to be skipped.

### Career profile
- Personal summary, education, experience, projects, skills, certifications, achievements, career preferences, documents.
- Editable structured data with provenance where possible.
- Resume parsing must never silently overwrite user-confirmed data.

### Career explorer
- Search and compare roles.
- Display responsibilities, skills, learning requirements, and progression.
- Explain recommendations using profile evidence and stated preferences.
- Market claims require current sources or must be labelled unavailable.

### Opportunities
- Search internships and jobs.
- Filter by location, work mode, type, experience, skills, deadline, and compensation when available.
- Save, dismiss, compare, and inspect opportunities.
- Display source URL, discovered time, last-verified time, and data completeness.
- Never fabricate listings or application statuses.

### Opportunity details
- Description, requirements, responsibilities, eligibility, location, compensation, deadline, company, source.
- Explain matching skills, missing skills, and eligibility checks.
- Provide external application link where available.
- External submission requires explicit user confirmation and must be supported by a verified workflow.

### Company intelligence
- Company overview, locations, industry, careers link, open roles, and sourced research.
- Show source and verification timestamps.
- Mark inferred or unavailable information clearly.

### Skill gap analysis
- Compare verified user skills with target-role requirements.
- Explain evidence for current skill level and missing requirements.
- Prioritize gaps by relevance and confidence.
- Do not present uncertain proficiency estimates as facts.

### Learning roadmap
- Milestones, resources, projects, practice tasks, estimated effort, and progress.
- Users can edit, reorder, complete, or remove milestones.
- Recommendations should link to identified skill gaps.

### Resume Studio
- Resume library, upload, parsing, structured preview, editable sections.
- Job-description-specific analysis and improvement suggestions.
- Explain ATS-related findings; do not promise an ATS pass or invent a universal ATS score.
- Export only formats actually implemented.

### Interview Lab
- Role-specific technical, behavioral, and HR practice.
- Question session, answer capture, feedback, and practice history.
- Feedback must separate observable answer evidence from subjective suggestions.

### Applications
- Track interested, saved, applied, assessment, interview, offer, rejected, and withdrawn states.
- Store dates, notes, links, reminders, and history.
- Status changes must be user-confirmed or sourced from a trusted integration.

### Career monitor
- Saved searches, target roles/companies, alert preferences, monitoring status, last checked time.
- Show monitoring failures and paused states honestly.

### AI Career Coach
- Context-aware chat using authorized profile and application context.
- Suggested prompts and links to relevant modules.
- Allow users to understand and manage which profile context is used.

### Activity and notifications
- Activity timeline for meaningful product events.
- Read/unread notifications and preference controls.
- Do not expose sensitive agent traces or internal prompts.

### Settings
- Account, career preferences, notifications, privacy, security, connected services, and data management.

## 1.7 Non-functional requirements

- Responsive desktop, tablet, and mobile.
- Accessible keyboard interaction and WCAG 2.2 AA contrast targets.
- Secure authentication and object-level authorization.
- Typed API contracts and validation.
- Observable backend and agent workflows.
- Graceful handling of provider outages, rate limits, timeouts, and partial results.
- No secrets in frontend bundles or logs.
- Data export/deletion processes subject to legal and technical requirements.

## 1.8 MVP prioritization

### P0 — Core release
- Authentication
- Onboarding and profile
- Resume upload and parsing review
- Career dashboard
- Opportunity discovery and details
- Explainable matching
- Skill gap analysis
- Applications tracker
- AI Career Coach basic workflow
- Settings and notifications
- Audit and observability

### P1 — Expansion
- Learning roadmap
- Resume optimization
- Company intelligence
- Interview Lab
- Career monitoring and scheduled alerts

### P2 — Advanced
- Opportunity comparison
- Advanced analytics
- More integrations
- Carefully controlled application assistance

## 1.9 Success metrics

Measure outcomes rather than vanity metrics:
- Onboarding completion rate.
- Percentage of users with reviewed profiles.
- Relevant opportunity save rate.
- Opportunity detail-to-save conversion.
- Application tracker activation.
- Resume analysis completion and user-rated usefulness.
- Learning milestone completion.
- Repeat weekly active use.
- Recommendation feedback and correction rate.
- Data freshness and source coverage.
- Agent workflow success, latency, and cost.

Do not optimize for number of agent calls or time spent chatting.
