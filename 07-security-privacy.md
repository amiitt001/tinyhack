# 7. Security and Privacy Requirements

## 7.1 Security baseline

- Use established authentication libraries and verified sessions.
- Enforce authorization server-side for every user-owned resource.
- Apply least privilege to service accounts and agent tools.
- Validate and normalize all input.
- Use CSRF protection where applicable.
- Apply rate limits to authentication, uploads, agent endpoints, and expensive operations.
- Use secure headers and appropriate cookie settings.
- Keep dependencies patched.
- Scan uploads and validate MIME type, extension, size, and content where feasible.

## 7.2 Secrets

- Never place Gemini, TinyFish, database, or signing secrets in frontend code.
- Use environment variables locally and a managed secret store in production.
- Never commit `.env` files.
- Redact secrets from logs and error messages.
- Rotate compromised credentials immediately.

## 7.3 Resume and document security

- Treat uploaded files as untrusted.
- Restrict file types and sizes.
- Store files in private storage.
- Use short-lived signed URLs when required.
- Avoid public buckets.
- Do not execute macros, scripts, or embedded content.
- Preserve original uploads separately from parsed/edited versions.
- Do not log resume contents.

## 7.4 Agent and prompt-injection security

External websites, job descriptions, resumes, and user-provided documents can contain malicious instructions.

Controls:
- Treat retrieved content as data, never as system instructions.
- Separate trusted policy from untrusted content.
- Give agents only narrowly scoped tools.
- Validate every tool argument.
- Enforce authorization inside tools, not just in prompts.
- Restrict outbound destinations where possible.
- Limit tool calls, execution time, and result sizes.
- Require confirmation for external side effects.
- Do not let retrieved content change agent permissions or system policy.

## 7.5 Application and external actions

- Drafting an application is not the same as submitting it.
- Show the exact action and relevant data before confirmation.
- Require an explicit user action for submission, messaging, or external account changes.
- Use idempotency controls where supported.
- Record action outcome and provider confirmation.
- If success cannot be verified, show an uncertain or failed state rather than success.

## 7.6 Privacy and user control

- Collect only data required for the feature.
- Explain why profile data is used for personalization.
- Scope agent context to the current task.
- Avoid sending unnecessary personal data to external providers.
- Provide controls for connected integrations and preferences.
- Define retention for documents, conversations, and telemetry.
- Support export/deletion workflows where required by applicable law and product policy.

## 7.7 Logging and audit

Log:
- Authentication and authorization outcomes.
- Important profile/document actions.
- Agent workflow start/end and safe metadata.
- External tool invocation outcome.
- Application status changes.
- Sensitive settings changes.

Do not log:
- Passwords or access tokens.
- Full resume contents.
- Full private conversations by default.
- Unredacted provider secrets.
- Unnecessary personal information.

## 7.8 Threat-model checklist

Test for:
- Broken object-level authorization.
- Cross-user data leakage.
- Prompt injection through documents and web pages.
- SSRF and unsafe URL fetching.
- Malicious uploads.
- Stored/reflected XSS.
- CSRF where applicable.
- Rate-limit bypass.
- Secret leakage.
- Duplicate external actions.
- Overly permissive agent tools.
- Insecure direct object references.
