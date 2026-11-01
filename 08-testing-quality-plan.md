# 8. Testing and Quality Plan

## 8.1 Quality gates

A feature is not complete because its screen renders. It must satisfy:
- Correct route and navigation.
- Responsive layout.
- Loading, empty, error, and success states.
- Form validation.
- Authorization.
- API integration or explicitly documented mock boundary.
- Accessibility checks.
- Tests for important behavior.

## 8.2 Test layers

### Unit tests
- Domain services.
- Validation schemas.
- Match scoring.
- Eligibility rules.
- Data normalization.
- Agent output validators.
- Permission checks.

### Integration tests
- API routes and database.
- Document upload/processing.
- ADK gateway with mocked model/tool boundaries.
- TinyFish adapter with mocked provider responses.
- Notification and application workflows.

### End-to-end tests
- Sign up/sign in.
- Onboarding.
- Upload and review resume.
- Browse and save opportunity.
- View match explanation.
- Create and update application.
- Run skill-gap workflow.
- Use AI Coach.
- Mobile navigation and forms.

### Agent evaluations
- Profile-specific personalization.
- Grounding and evidence references.
- Hallucination resistance.
- Missing-data behavior.
- Prompt-injection resistance.
- Tool permission enforcement.
- Timeout and provider-failure behavior.
- Output schema validity.
- Cost and latency budgets.

## 8.3 Required test cases

1. Two users with different profiles receive appropriately different recommendations.
2. A user cannot retrieve another user's resume or application.
3. Missing resume fields are not fabricated.
4. An expired opportunity is not presented as verified active.
5. An opportunity match includes score components and explanation.
6. An agent cannot invoke a tool outside its permissions.
7. Malicious instructions inside a job description do not alter system behavior.
8. A provider timeout results in a recoverable state.
9. Retrying a safe job does not duplicate records.
10. Application submission is never represented as successful without verified confirmation.
11. Mobile layouts have no unintended horizontal overflow.
12. Keyboard users can operate navigation, forms, dialogs, and menus.

## 8.4 Visual QA

- Compare implementation with Stitch designs.
- Verify typography, spacing, colors, and component states.
- Test at common desktop, tablet, and mobile widths.
- Check contrast and focus visibility.
- Check long text, empty data, and localization edge cases.
- Verify chart labels and table overflow.

## 8.5 Release gate

Before marking a phase complete:
- Build passes.
- Lint passes.
- Type check passes.
- Relevant unit/integration/E2E tests pass.
- No known critical authorization or data-isolation defect.
- No broken primary journey.
- Known limitations are documented.
