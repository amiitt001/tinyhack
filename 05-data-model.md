# 5. Data Model and Persistence

## 5.1 Principles

This is a proposed logical model. Reconcile it with the existing schema and ORM before creating migrations.

- Use stable primary keys.
- Store timestamps in UTC.
- Enforce ownership at the database/service boundary.
- Preserve original uploaded documents.
- Track provenance for extracted and externally sourced information.
- Prefer normalized relational data for core entities.
- Use JSON only for genuinely variable structured payloads.
- Use vector embeddings only for a defined retrieval use case.

## 5.2 Core entities

### User and profile
- `users`: identity-provider subject, email, account status, timestamps.
- `career_profiles`: user ID, summary, career stage, preferences, completion state.
- `educations`: institution, qualification, field, start/end dates, grade if supplied.
- `experiences`: organization, role, description, dates.
- `projects`: title, description, technologies, links, dates.
- `skills`: canonical skill catalog.
- `user_skills`: user, skill, proficiency evidence, source, confidence, last verified.
- `certifications`: issuer, credential, issue/expiry dates, credential URL.
- `career_preferences`: target roles, locations, work modes, employment types.

### Documents and resumes
- `documents`: owner, storage key, filename, MIME type, size, checksum, processing status.
- `resumes`: document reference, parsed version, active flag.
- `resume_sections`: structured section content and ordering.
- `resume_parse_runs`: parser version, status, warnings, timestamps.
- `profile_evidence`: field, value/reference, source document, user-confirmed flag.

### Career intelligence
- `career_roles`: canonical role catalog and metadata.
- `role_skill_requirements`: role, skill, importance, requirement type, source.
- `career_analyses`: owner, target role, output, evidence references, model/workflow metadata.
- `skill_gap_analyses`: owner, role, gap data, timestamp.
- `learning_roadmaps`: owner, target, status, version.
- `learning_milestones`: roadmap, title, skill, sequence, status, estimated effort.
- `learning_resources`: title, provider, URL, type, verification metadata.

### Opportunities and companies
- `companies`: canonical company identity and known metadata.
- `opportunities`: company, title, description, location, work mode, employment type, compensation, deadline, source URL, discovered time, last verified time, status.
- `opportunity_skills`: opportunity, skill, requirement type.
- `saved_opportunities`: user, opportunity, saved time.
- `opportunity_matches`: user, opportunity, deterministic score components, explanation, scoring version, evaluated time.
- `company_research_runs`: company, source references, findings, timestamps.

### Applications
- `applications`: user, opportunity reference or manual job, status, applied date, next action date, notes.
- `application_events`: application, previous status, new status, actor, timestamp, source.
- `application_reminders`: application, due date, status.

### Interview and conversations
- `interview_sessions`: user, target role, interview type, status, timestamps.
- `interview_questions`: session, prompt, category, rubric.
- `interview_answers`: question, answer, feedback, criteria scores.
- `conversations`: user, title, context scope, timestamps.
- `messages`: conversation, role, content, metadata, timestamps.

### Operations
- `notifications`: user, type, title, body, read state, action reference.
- `activity_events`: user, event type, safe metadata, timestamp.
- `monitoring_rules`: user, criteria, enabled state, last checked.
- `agent_runs`: user, workflow, status, duration, safe metadata, correlation ID.
- `audit_events`: actor, action, resource, outcome, timestamp.

## 5.3 Relationships

- One user owns one primary career profile.
- One user may own multiple resumes and documents.
- A resume may have multiple parse runs and revisions.
- Users have many skills, projects, education records, and experiences.
- Opportunities may belong to one company and have many required skills.
- Users may save many opportunities.
- Users may have one or more match evaluations per opportunity over time.
- Applications belong to users and may reference an opportunity.
- Applications have many status events and reminders.
- Learning roadmaps contain ordered milestones.
- Interview sessions contain questions and answers.

## 5.4 Data provenance

For extracted or external facts, preserve where they came from:
- `source_type`
- `source_reference`
- `source_url` when applicable
- `extracted_at`
- `last_verified_at`
- `confidence` only when meaningful and calibrated
- `user_confirmed`

Do not use confidence values as decorative certainty scores.

## 5.5 Matching model

Use deterministic scoring with documented components. Example dimensions:
- Required-skill coverage.
- Preferred-skill coverage.
- Eligibility fit.
- Location/work-mode fit.
- Experience fit.

Weights must be configurable, versioned, and evaluated. Do not let an LLM invent the final numeric score. An LLM may explain the result using evidence supplied by the scoring service.

## 5.6 Retention and deletion

Define retention rules for resumes, conversations, agent traces, and external research. Support account data export/deletion where required. Avoid storing full document contents in logs or agent telemetry.
