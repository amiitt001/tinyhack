# SkillSphere V3

A responsive, dark-first career workspace built with React, TypeScript, Vite, Tailwind CSS, and Lucide icons.

```sh
npm ci
npm run dev
```

Validation: `npm run build`, `npm run lint`, `npm run typecheck`, `npm test`.
Browser tests use `/usr/bin/chromium`; adjust `playwright.config.ts` for another installation.

This is a local-first frontend prototype. There is no authentication backend, AI service, live opportunity feed, resume parser, or background monitoring. Optional fictional demo content is explicitly labeled. Profile edits, application tracking, learning tasks, resume drafts, and preferences work locally. Do not store sensitive information on shared devices.

See [the design and implementation report](docs/skillsphere-v3-ui-design.md).

The latest UI pass applies the 21st.dev-inspired component selection to the existing charcoal/orange product identity. See `design.md` for the current dashboard composition, data behavior, and responsive rules. Source changes are in `src/pages/Overview.tsx`, `src/components/Layout.tsx`, and `src/refinements.css`.
