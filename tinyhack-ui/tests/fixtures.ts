import { test as base, expect, type Page } from "@playwright/test";
import type {
  DiscoveryInput,
  DiscoveryRun,
  Opportunity,
  Source,
} from "../src/lib/opportunities";

export const RUN_ID = "20000000-0000-4000-8000-000000000001";
export const jobs: Opportunity[] = [
  "Python Developer Intern",
  "Frontend Engineer",
  "Data Analyst",
  "Product Engineer",
  "Platform Engineer",
  "Graduate Software Engineer",
  "Developer Advocate",
].map((title, index) => ({
  id: `10000000-0000-4000-8000-${String(index + 1).padStart(12, "0")}`,
  title,
  company_name: "Canonical",
  description:
    "Synthetic browser-test fixture. Build reliable tools, collaborate with a thoughtful team, and explain your engineering decisions.",
  location: "Delhi NCR, IN",
  work_mode: "remote",
  employment_type: "internship",
  experience_requirement: "Early career",
  required_skills: ["Python", "SQL"],
  preferred_skills: null,
  salary_min: index === 0 ? "20000.00" : null,
  salary_max: index === 0 ? "30000.00" : null,
  salary_currency: index === 0 ? "INR" : null,
  salary_unit: index === 0 ? "MONTH" : null,
  stipend: null,
  application_url: `https://canonical.com/careers/${100 + index}`,
  canonical_url: `https://canonical.com/careers/${100 + index}`,
  source_url: `https://canonical.com/careers/${100 + index}`,
  source_id: "30000000-0000-4000-8000-000000000001",
  source_external_id: String(100 + index),
  deadline: null,
  discovered_at: "2026-11-01T08:00:00Z",
  last_verified_at: "2026-11-01T08:00:00Z",
  last_attempted_at: "2026-11-01T08:00:00Z",
  expires_at: null,
  status: "validated",
  extraction_status: "validated",
  content_hash: null,
  sources: [
    {
      source_id: "30000000-0000-4000-8000-000000000001",
      original_url: `https://canonical.com/careers/${100 + index}`,
      canonical_url: `https://canonical.com/careers/${100 + index}`,
      observed_at: "2026-11-01T08:00:00Z",
      validation_status: "accepted",
    },
  ],
}));
export type MockOptions = {
  source?: "enabled" | "configured" | "offline" | "unauthorized";
  statuses?: DiscoveryRun["status"][];
  createFailure?: boolean;
  creationError?: { status: number; detail: unknown };
  resultFailure?: boolean;
  savedFailure?: boolean;
  singleJob?: boolean;
  expired?: boolean;
};
export async function mockBackend(page: Page, options: MockOptions = {}) {
  let profile = {
    id: "profile-1",
    user_id: "test-user",
    summary: null as string | null,
    career_stage: null as string | null,
    completion_percent: 0,
  };
  const saved = new Set<string>();
  const keys: string[] = [];
  let input: DiscoveryInput | null = null;
  let reads = 0;
  let status: DiscoveryRun["status"] = "pending";
  let failCreate = options.createFailure || false;
  let resultFailure = options.resultFailure || false;
  let failSaved = options.savedFailure || false;
  let created = false;
  const sourceNames = [
    "official_company_careers",
    "linkedin_jobs",
    "internshala",
    "naukri",
    "wellfound",
  ];
  const sources: Source[] = sourceNames.map((name, index) => ({
    name,
    status:
      index === 0
        ? options.source === "enabled"
          ? "enabled"
          : "configured"
        : index === 4
          ? "unavailable"
          : "restricted",
    supported: index === 0,
    configured: index === 0,
    allowed_domains: [index === 0 ? "canonical.com" : `${name}.invalid`],
    behavior: "search_then_jsonld_detail",
    attribution: "Original source",
    validation_policy: "Source evidence",
    access_restrictions: "Public approved pages only",
  }));
  const data = options.singleJob ? jobs.slice(0, 1) : jobs;
  const makeRun = (): DiscoveryRun => ({
    id: RUN_ID,
    user_id: "test-user",
    query: input?.query || "Python Developer Intern",
    location: input?.location || null,
    employment_type: input?.employment_type || null,
    experience_level: input?.experience_level || null,
    requested_sources: ["official_company_careers"],
    status,
    total_results: ["pending", "running"].includes(status)
      ? 0
      : status === "failed"
        ? 1
        : data.length + (status === "partially_completed" ? 1 : 0),
    accepted_results: ["pending", "running", "failed"].includes(status)
      ? 0
      : data.length,
    rejected_results:
      status === "failed" || status === "partially_completed" ? 1 : 0,
    attempt_count: 1,
    started_at: null,
    completed_at: null,
    error_code: status === "failed" ? "no_validated_results" : null,
    safe_error_message: null,
    created_at: "2026-11-01T08:00:00Z",
    updated_at: "2026-11-01T08:00:00Z",
  });
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace("/api/v1", "");
    const json = (body: unknown, responseStatus = 200) =>
      route.fulfill({ status: responseStatus, json: body });
    if (path === "/career-profile") {
      if (request.method() === "PUT")
        profile = { ...profile, ...request.postDataJSON() };
      return json(profile);
    }
    if (path === "/resumes" || path === "/career-analysis") return json([]);
    if (path === "/opportunity-sources") {
      if (options.source === "offline") return route.abort();
      if (options.source === "unauthorized")
        return json({ detail: "Invalid authentication token" }, 401);
      return json(sources);
    }
    if (path === "/opportunity-discoveries" && request.method() === "POST") {
      keys.push(request.headers()["idempotency-key"]);
      input = request.postDataJSON();
      created = true;
      if (options.creationError)
        return json(
          { detail: options.creationError.detail },
          options.creationError.status,
        );
      if (failCreate) {
        failCreate = false;
        return route.abort();
      }
      return json(makeRun(), 202);
    }
    if (path === `/opportunity-discoveries/${RUN_ID}`) {
      const sequence = options.statuses || ["completed"];
      status = sequence[Math.min(reads++, sequence.length - 1)];
      return json(makeRun());
    }
    if (
      path === `/opportunity-discoveries/${RUN_ID}/results` ||
      path === "/opportunities/saved"
    ) {
      if (path.endsWith("/results") && resultFailure) {
        resultFailure = false;
        return json(
          {
            detail: {
              code: "temporarily_unavailable",
              message: "Results are temporarily unavailable.",
            },
          },
          503,
        );
      }
      const offset = Number(url.searchParams.get("offset") || 0),
        limit = Number(url.searchParams.get("limit") || 20);
      const all =
        path === "/opportunities/saved"
          ? data.filter((job) => saved.has(job.id))
          : ["pending", "running", "failed"].includes(status)
            ? []
            : data;
      return json({
        items: all.slice(offset, offset + limit),
        total: all.length,
        offset,
        limit,
        has_more: offset + limit < all.length,
      });
    }
    const save = path.match(/^\/opportunities\/([^/]+)\/save$/);
    if (save) {
      if (failSaved) {
        failSaved = false;
        return json(
          {
            detail: {
              code: "save_unavailable",
              message: "Saving is temporarily unavailable.",
            },
          },
          503,
        );
      }
      const isSaved = request.method() === "POST";
      if (isSaved) saved.add(save[1]);
      else saved.delete(save[1]);
      return json({ opportunity_id: save[1], saved: isSaved });
    }
    const detail = path.match(/^\/opportunities\/([^/]+)$/);
    if (detail) {
      const job = data.find((job) => job.id === detail[1]);
      return job
        ? json({
            ...job,
            ...(options.expired ? { expires_at: "2020-01-01T00:00:00Z" } : {}),
          })
        : json(
            {
              detail: {
                code: "not_found",
                message: "Validated opportunity not found",
              },
            },
            404,
          );
    }
    return json({ detail: "Not found" }, 404);
  });
  return {
    keys,
    saved,
    get input() {
      return input;
    },
    get reads() {
      return reads;
    },
    get created() {
      return created;
    },
  };
}
export const test = base.extend<{
  backend: Awaited<ReturnType<typeof mockBackend>>;
}>({
  backend: [
    async ({ page }, use) => {
      await use(await mockBackend(page));
    },
    { auto: true },
  ],
});
export { expect };
