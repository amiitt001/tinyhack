import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import {
  ApiError,
  fetchProfile,
  fetchAnalyses,
  fetchIntegrationStatus,
  fetchResumes,
  saveProfile,
  type BackendResume,
  type CareerAnalysis,
  type IntegrationStatus,
} from './api';

export interface Profile {
  name: string;
  role: string;
  location: string;
  education: string;
  skills: string;
  experience: string;
  projects: string;
  interests: string;
}
export interface Application {
  id: string;
  company: string;
  role: string;
  status: string;
  date: string;
  notes: string;
  reminder: string;
}
export interface Notice {
  id: string;
  title: string;
  detail: string;
  read: boolean;
}
interface State {
  profile: Profile;
  resumes: BackendResume[];
  analysis: CareerAnalysis | null;
  analyses: CareerAnalysis[];
  backendLoading: boolean;
  backendError: string;
  integrationStatus: IntegrationStatus | null;
  saved: string[];
  completed: string[];
  applications: Application[];
  notices: Notice[];
  activity: string[];
  monitors: string[];
  demo: boolean;
  preferences: Record<string, boolean>;
}

const initial: State = {
  profile: {
    name: '',
    role: '',
    location: '',
    education: '',
    skills: '',
    experience: '',
    projects: '',
    interests: '',
  },
  resumes: [],
  analysis: null,
  analyses: [],
  backendLoading: true,
  backendError: '',
  integrationStatus: null,
  saved: [],
  completed: [],
  applications: [],
  notices: [],
  activity: [],
  monitors: [],
  demo: false,
  preferences: { email: true, deadlines: true, learning: false },
};

function readLocalState(): Pick<
  State,
  'saved' | 'completed' | 'applications' | 'notices' | 'activity' | 'monitors' | 'demo' | 'preferences'
> {
  try {
    const stored = localStorage.getItem('skillsphere-v3');
    const parsed = stored ? JSON.parse(stored) : {};
    return {
      saved: parsed.saved || [],
      completed: parsed.completed || [],
      applications: parsed.applications || [],
      notices: parsed.notices || [],
      activity: parsed.activity || [],
      monitors: parsed.monitors || [],
      demo: parsed.demo || false,
      preferences: parsed.preferences || initial.preferences,
    };
  } catch {
    return {
      saved: [],
      completed: [],
      applications: [],
      notices: [],
      activity: [],
      monitors: [],
      demo: false,
      preferences: initial.preferences,
    };
  }
}

const Context = createContext<{
  state: State;
  update: (patch: Partial<State>) => void;
  log: (text: string) => void;
  toast: (text: string) => void;
  message: string;
}>({ state: { ...initial, ...readLocalState() }, update: () => {}, log: () => {}, toast: () => {}, message: '' });

export function Provider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<State>(() => ({ ...initial, ...readLocalState() }));
  const [message, setMessage] = useState('');

  useEffect(() => {
    let active = true;
    Promise.allSettled([fetchProfile(), fetchResumes(), fetchAnalyses(), fetchIntegrationStatus()]).then(([profileResult, resumesResult, analysesResult, integrationResult]) => {
      if (!active) return;
      const profile = profileResult.status === 'fulfilled' ? profileResult.value : null;
      const resumes = resumesResult.status === 'fulfilled' ? resumesResult.value : [];
      const analyses = analysesResult.status === 'fulfilled' ? analysesResult.value : [];
      const integrationStatus = integrationResult.status === 'fulfilled' ? integrationResult.value : null;
      let remoteProfile: Profile | undefined;
      if (profile?.summary) {
        try {
          remoteProfile = { ...initial.profile, ...(JSON.parse(profile.summary) as Partial<Profile>) };
        } catch {
          setMessage('Profile data from the backend could not be read.');
        }
      }
      const failed = [profileResult, resumesResult, analysesResult, integrationResult].some(
        (result) =>
          result.status === 'rejected' &&
          !(result.reason instanceof ApiError && result.reason.status === 404),
      );
      setState((current) => ({
        ...current,
        ...(remoteProfile ? { profile: remoteProfile } : {}),
        resumes,
        analyses,
        analysis: analyses[0] || null,
        backendLoading: false,
        backendError: failed ? 'Some backend data could not be loaded.' : '',
        integrationStatus,
      }));
    });
    return () => {
      active = false;
    };
  }, []);

  function update(patch: Partial<State>) {
    setState((current) => {
      const next = { ...current, ...patch };
      const localPatch = { ...patch };
      delete localPatch.profile;
      delete localPatch.resumes;
      delete localPatch.analysis;
      delete localPatch.backendLoading;
      delete localPatch.backendError;
      try {
        localStorage.setItem('skillsphere-v3', JSON.stringify({ ...current, ...localPatch }));
      } catch {
        setMessage('Storage unavailable. Changes will last for this session only.');
      }
      if (patch.profile) {
        const complete = Object.values(next.profile).filter(Boolean).length;
        saveProfile({
          summary: JSON.stringify(next.profile),
          career_stage: 'development',
          completion_percent: Math.round((complete / 8) * 100),
        }).catch(() => setMessage('Profile could not be saved to the backend.'));
      }
      return next;
    });
  }

  function toast(text: string) {
    setMessage(text);
    window.setTimeout(() => setMessage(''), 4000);
  }

  function log(text: string) {
    setState((current) => {
      const next = { ...current, activity: [`${new Date().toLocaleString()} · ${text}`, ...current.activity] };
      try {
        localStorage.setItem(
          'skillsphere-v3',
          JSON.stringify({
            saved: next.saved,
            completed: next.completed,
            applications: next.applications,
            notices: next.notices,
            activity: next.activity,
            monitors: next.monitors,
            demo: next.demo,
            preferences: next.preferences,
          }),
        );
      } catch {
        // The current session remains usable.
      }
      return next;
    });
  }

  return (
    <Context.Provider value={{ state, update, log, toast, message }}>
      {children}
      <div className={`toast ${message ? 'visible' : ''}`} role="status">
        {message}
      </div>
    </Context.Provider>
  );
}

export const useApp = () => useContext(Context);

export const stages = ['Interested', 'Saved', 'Applied', 'Assessment', 'Interview', 'Offer', 'Rejected'];
export const opportunities = [
  { id: 'frontend', company: 'Forma Labs', initial: 'F', role: 'Frontend Engineering Intern', location: 'Bengaluru', mode: 'Hybrid', type: 'Internship', skills: ['React', 'TypeScript', 'CSS'], description: 'Build thoughtful interfaces for a collaborative design workspace.', pay: '₹25k–35k / month', color: 'purple' },
  { id: 'product', company: 'Orbit Studio', initial: 'O', role: 'Junior Product Engineer', location: 'Remote', mode: 'Remote', type: 'Full-time', skills: ['React', 'JavaScript', 'Git'], description: 'Work across product design and engineering on tools for creative teams.', pay: 'Not provided', color: 'blue' },
  { id: 'data', company: 'Metric Works', initial: 'M', role: 'Data Science Intern', location: 'Hyderabad', mode: 'On-site', type: 'Internship', skills: ['Python', 'SQL', 'Statistics'], description: 'Explore datasets and communicate useful patterns with a small analytics team.', pay: '₹20k–30k / month', color: 'green' },
];
export const milestones = [
  { id: 'foundations', title: 'Strengthen your foundations', label: 'FOUNDATION', time: '1–2 weeks', tasks: ['Review JavaScript fundamentals', 'Practice Git and collaboration', 'Build an accessible form'] },
  { id: 'react', title: 'Build with React & TypeScript', label: 'CORE SKILLS', time: '2–3 weeks', tasks: ['Understand component composition', 'Model data with TypeScript', 'Build a small dashboard'] },
  { id: 'project', title: 'Ship a portfolio project', label: 'PUT IT INTO PRACTICE', time: '2 weeks', tasks: ['Define a real user problem', 'Implement and test the workflow', 'Write a project case study'] },
  { id: 'interview', title: 'Get interview ready', label: 'NEXT CHAPTER', time: '1–2 weeks', tasks: ['Practice explaining tradeoffs', 'Review common technical questions', 'Prepare your project walkthrough'] },
];
