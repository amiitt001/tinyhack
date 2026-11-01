import { request } from "./api";

export type DiscoveryStatus =
  | "pending"
  | "running"
  | "completed"
  | "partially_completed"
  | "failed"
  | "cancelled";
export type Source = {
  name: string;
  status:
    | "configured"
    | "supported"
    | "enabled"
    | "disabled"
    | "restricted"
    | "unavailable";
  supported: boolean;
  configured: boolean;
  allowed_domains: string[];
  behavior: string;
  attribution: string;
  validation_policy: string;
  access_restrictions: string;
};
export type DiscoveryInput = {
  query: string;
  location: string | null;
  employment_type:
    | "full_time"
    | "part_time"
    | "internship"
    | "contract"
    | "temporary"
    | "volunteer"
    | "other"
    | null;
  experience_level: string | null;
  skills: string[];
  sources: string[];
};
export type DiscoveryRun = {
  id: string;
  user_id: string;
  query: string;
  location: string | null;
  employment_type: string | null;
  experience_level: string | null;
  requested_sources: string[];
  status: DiscoveryStatus;
  total_results: number;
  accepted_results: number;
  rejected_results: number;
  attempt_count: number;
  started_at: string | null;
  completed_at: string | null;
  error_code: string | null;
  safe_error_message: string | null;
  created_at: string;
  updated_at: string;
};
export type Opportunity = {
  id: string;
  title: string;
  company_name: string | null;
  description: string | null;
  location: string | null;
  work_mode: string | null;
  employment_type: string | null;
  experience_requirement: string | null;
  required_skills: string[] | null;
  preferred_skills: string[] | null;
  salary_min: string | number | null;
  salary_max: string | number | null;
  salary_currency: string | null;
  salary_unit: string | null;
  stipend: string | null;
  application_url: string | null;
  canonical_url: string | null;
  source_url: string;
  source_id: string | null;
  source_external_id: string | null;
  deadline: string | null;
  discovered_at: string;
  last_verified_at: string | null;
  last_attempted_at: string | null;
  expires_at: string | null;
  status: string;
  extraction_status: string | null;
  content_hash: string | null;
  sources: Array<{
    source_id: string;
    original_url: string | null;
    canonical_url: string | null;
    observed_at: string;
    validation_status: string;
  }>;
};
export type OpportunityPage = {
  items: Opportunity[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
};
export const PAGE_SIZE = 6;
export const validId = (value: string) =>
  /^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i.test(value);
export const activeRun = (run: DiscoveryRun | null) =>
  !!run && ["pending", "running"].includes(run.status);
export const sourceName = (name: string) =>
  ({
    official_company_careers: "Official company careers",
    linkedin_jobs: "LinkedIn Jobs",
    internshala: "Internshala",
    naukri: "Naukri",
    wellfound: "Wellfound",
  })[name] || name.replaceAll("_", " ");
export const sourceLabel = (source: Source) =>
  ({
    enabled: "Available",
    configured: "Setup needed",
    supported: "Not enabled",
    disabled: "Paused",
    restricted: "Restricted",
    unavailable: "Unavailable",
  })[source.status];
export function formatDate(value: string | null, fallback = "Not provided") {
  if (!value || !Number.isFinite(Date.parse(value))) return fallback;
  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}
export function safeExternalUrl(value: string | null) {
  try {
    const url = new URL(value || "");
    return url.protocol === "https:" && !url.username && !url.password
      ? url.href
      : null;
  } catch {
    return null;
  }
}
export function sourceHost(value: string | null) {
  const safe = safeExternalUrl(value);
  return safe
    ? new URL(safe).hostname.replace(/^www\./, "")
    : "Source unavailable";
}
export function compensation(job: Opportunity) {
  const amounts = [job.salary_min, job.salary_max].filter(
    (value): value is string | number => value !== null,
  );
  if (!amounts.length) return job.stipend || "Compensation not listed";
  const format = (value: string | number) => {
    const number = Number(value);
    if (!Number.isFinite(number)) return "Not provided";
    try {
      return new Intl.NumberFormat("en", {
        maximumFractionDigits: 0,
        ...(job.salary_currency
          ? { style: "currency", currency: job.salary_currency }
          : {}),
      }).format(number);
    } catch {
      return `${number.toLocaleString("en")} ${job.salary_currency || ""}`.trim();
    }
  };
  const range =
    amounts.length > 1 && amounts[0] !== amounts[1]
      ? `${format(amounts[0])} – ${format(amounts[1])}`
      : format(amounts[0]);
  const units: Record<string, string> = {
    HOUR: "hour",
    DAY: "day",
    WEEK: "week",
    MONTH: "month",
    YEAR: "year",
  };
  return `${range}${job.salary_unit ? ` / ${units[job.salary_unit.toUpperCase()] || job.salary_unit.toLowerCase()}` : " · period not listed"}${job.salary_currency ? "" : " · currency not listed"}`;
}
export const fetchSources = (signal?: AbortSignal) =>
  request<Source[]>("/opportunity-sources", { signal });
export const createDiscovery = (
  input: DiscoveryInput,
  key: string,
  signal?: AbortSignal,
) =>
  request<DiscoveryRun>("/opportunity-discoveries", {
    method: "POST",
    headers: { "Idempotency-Key": key },
    body: JSON.stringify(input),
    signal,
  });
export const fetchDiscovery = (id: string, signal?: AbortSignal) =>
  request<DiscoveryRun>(`/opportunity-discoveries/${encodeURIComponent(id)}`, {
    signal,
  });
export const fetchResults = (
  id: string,
  offset: number,
  signal?: AbortSignal,
) =>
  request<OpportunityPage>(
    `/opportunity-discoveries/${encodeURIComponent(id)}/results?limit=${PAGE_SIZE}&offset=${offset}`,
    { signal },
  );
export const fetchSaved = (
  offset = 0,
  limit = PAGE_SIZE,
  signal?: AbortSignal,
) =>
  request<OpportunityPage>(
    `/opportunities/saved?limit=${limit}&offset=${offset}`,
    { signal },
  );
export const fetchOpportunity = (id: string, signal?: AbortSignal) =>
  request<Opportunity>(`/opportunities/${encodeURIComponent(id)}`, { signal });
export const setOpportunitySaved = (id: string, saved: boolean) =>
  request<{ opportunity_id: string; saved: boolean }>(
    `/opportunities/${encodeURIComponent(id)}/save`,
    { method: saved ? "POST" : "DELETE" },
  );
