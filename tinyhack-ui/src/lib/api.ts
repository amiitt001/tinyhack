const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const TOKEN_KEY = 'skillsphere-v3-token';
const REQUEST_TIMEOUT_MS = 30_000;

export class ApiError extends Error {
  constructor(message: string, readonly status?: number) {
    super(message);
    this.name = 'ApiError';
  }
}

export type BackendProfile = {
  id: string;
  user_id: string;
  summary: string | null;
  career_stage: string | null;
  completion_percent: number;
};

export type BackendResume = {
  id: string;
  filename: string;
  status: string;
  created_at: string;
  parse_error: string | null;
  parsed_data: {
    name?: string;
    email?: string;
    technical_skills?: string[];
    projects?: string[];
  } | null;
};

export type CareerAnalysis = {
  id: string;
  resume_id: string | null;
  status: string;
  created_at: string;
  career_paths: Array<{
    title: string;
    explanation: string;
    strengths: string[];
    skill_gaps: string[];
    learning_priorities: string[];
    next_steps: string[];
  }>;
  limitations: string[];
};

export function getToken(): string {
  const existing = localStorage.getItem(TOKEN_KEY);
  if (existing) return existing;
  const token = `dev:${import.meta.env.VITE_DEV_USER_ID || 'local-ui-user'}`;
  localStorage.setItem(TOKEN_KEY, token);
  return token;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${getToken()}`,
        ...(init.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...init.headers,
      },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('The backend request timed out. Please try again.');
    }
    throw new ApiError('The backend is unavailable. Check that the API is running.');
  } finally {
    window.clearTimeout(timeout);
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      body.detail || `Backend request failed (${response.status})`,
      response.status,
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

export function fetchProfile() {
  return request<BackendProfile>('/career-profile');
}

export function fetchIntegrationStatus() {
  return request<IntegrationStatus>('/integrations');
}

export type IntegrationStatus = {
  status: string;
  gemini: { configured: boolean; model: string };
  tinyfish: { configured: boolean; agent_enabled: boolean };
  supabase: { configured: boolean; storage_backend: string };
};

export function sendCoachMessage(message: string, profileSummary: string) {
  return request<{ response: string; model: string }>('/coach', {
    method: 'POST',
    body: JSON.stringify({ message, profile_summary: profileSummary }),
  });
}

export type CareerComparison = {
  first_career: string;
  second_career: string;
  summary: string;
  career_a_fit: string;
  career_b_fit: string;
  shared_skills: string[];
  tradeoffs: string[];
  recommended_next_step: string;
  limitations: string[];
  model: string;
};

export function compareCareers(
  firstCareer: string,
  secondCareer: string,
  profileSummary: string,
) {
  return request<CareerComparison>('/career-comparisons', {
    method: 'POST',
    body: JSON.stringify({
      first_career: firstCareer,
      second_career: secondCareer,
      profile_summary: profileSummary,
    }),
  });
}

export function fetchResumes() {
  return request<BackendResume[]>('/resumes');
}

export function deleteResume(resumeId: string) {
  return request<void>(`/resumes/${encodeURIComponent(resumeId)}`, { method: 'DELETE' });
}

export function fetchAnalyses(limit = 20, offset = 0) {
  return request<CareerAnalysis[]>(
    `/career-analysis?limit=${limit}&offset=${offset}`,
  );
}

export function fetchAnalysis(analysisId: string) {
  return request<CareerAnalysis>(`/career-analysis/${encodeURIComponent(analysisId)}`);
}

export function saveProfile(profile: {
  summary: string;
  career_stage: string;
  completion_percent: number;
}) {
  return request<BackendProfile>('/career-profile', {
    method: 'PUT',
    body: JSON.stringify(profile),
  });
}

export function uploadResume(file: File) {
  const body = new FormData();
  body.append('file', file);
  return request<BackendResume>('/resumes', { method: 'POST', body });
}

export function createCareerAnalysis(resumeId: string) {
  return request<CareerAnalysis>(
    `/career-analysis?resume_id=${encodeURIComponent(resumeId)}`,
    { method: 'POST' },
  );
}

export type DiscoveryRun = {
  id: string;
  user_id: string;
  status: string;
  query: string;
  location: string | null;
  employment_type: string | null;
  experience_level: string | null;
  total_results: number | null;
  accepted_results: number | null;
  rejected_results: number | null;
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
  application_url: string | null;
  canonical_url: string | null;
  source_url: string;
  status: string;
  extraction_status: string;
  is_verified: boolean;
  discovered_at: string;
};

export type PaginatedOpportunities = {
  items: Opportunity[];
  total: number;
  limit: number;
  offset: number;
};

export function createDiscovery(body: {
  query: string;
  location?: string;
  employment_type?: string;
  experience_level?: string;
  skills?: string[];
  sources?: string[];
  idempotency_key?: string;
  refresh?: boolean;
}) {
  return request<DiscoveryRun>('/opportunity-discoveries', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function fetchDiscovery(runId: string) {
  return request<DiscoveryRun>(`/opportunity-discoveries/${encodeURIComponent(runId)}`);
}

export function fetchDiscoveryResults(runId: string, limit = 20, offset = 0) {
  return request<PaginatedOpportunities>(
    `/opportunity-discoveries/${encodeURIComponent(runId)}/results?limit=${limit}&offset=${offset}`,
  );
}

export function fetchOpportunity(opportunityId: string) {
  return request<Opportunity>(`/opportunities/${encodeURIComponent(opportunityId)}`);
}

export function saveOpportunity(opportunityId: string, notes?: string) {
  return request(`/opportunities/${encodeURIComponent(opportunityId)}/save`, {
    method: 'POST',
    body: JSON.stringify({ notes: notes ?? null }),
  });
}

export function deleteSavedOpportunity(opportunityId: string) {
  return request<void>(`/opportunities/${encodeURIComponent(opportunityId)}/save`, {
    method: 'DELETE',
  });
}

export type TinyFishSearchResult = {
  position: number;
  title: string;
  url: string;
  site_name: string;
  snippet: string;
  date: string | null;
  publisher: string | null;
};

export function searchOpportunities(query: string, location?: string, page = 0) {
  return request<{
    query: string;
    results: TinyFishSearchResult[];
    total_results: number;
    page: number;
  }>('/opportunity-tools/search', {
    method: 'POST',
    body: JSON.stringify({ query, location, page }),
  });
}

export function fetchOpportunityPage(url: string) {
  return request<{
    url: string;
    final_url: string | null;
    title: string | null;
    text: string;
    latency_ms: number | null;
  }>('/opportunity-tools/fetch', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
}
