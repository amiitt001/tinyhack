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
