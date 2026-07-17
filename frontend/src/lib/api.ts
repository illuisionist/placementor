/**
 * PlaceMentor AI — API Client (TypeScript)
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface StudentProfile {
  id?: string;
  user_id?: string;
  branch?: string;
  semester?: number;
  cgpa?: number;
  graduation_year?: number;
  skills?: string[];
  preferred_companies?: string[];
  preferred_domains?: string[];
  leetcode_handle?: string;
  github_handle?: string;
  linkedin_url?: string;
}

export interface ChatResponse {
  response: string;
  intent?: string;
  session_id?: string;
  suggested_next_action?: string;
  next_action?: string;
}

export interface RoadmapWeek {
  week: number;
  theme?: string;
  goals?: string[];
  dsa?: { topics?: string[]; problems_target?: number };
  core_subjects?: { subject: string; topics?: string[] }[];
  aptitude?: string;
  projects?: string;
  mock_interview?: boolean;
  checkpoint?: string;
}

export interface Roadmap {
  id?: string;
  title?: string;
  target_company?: string;
  target_role?: string;
  duration_weeks?: number;
  current_week?: number;
  completion_pct?: number;
  weeks_plan?: RoadmapWeek[];
}

export interface MockInterview {
  id: string;
  interview_type: string;
  target_company?: string;
  overall_score?: number;
  status: string;
  created_at: string;
}

export interface Resume {
  id: string;
  original_name: string;
  version: number;
  is_active: boolean;
  ats_score?: number;
  strengths?: string[];
  weaknesses?: string[];
  suggestions?: Array<{ priority: string; suggestion: string; fix?: string }>;
  uploaded_at: string;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const getToken = (): string | null =>
  typeof window !== 'undefined' ? localStorage.getItem('pm_token') : null;

export const setToken = (token: string): void =>
  localStorage.setItem('pm_token', token);

export const setUser = (user: User): void =>
  localStorage.setItem('pm_user', JSON.stringify(user));

export const getUser = (): User | null => {
  if (typeof window === 'undefined') return null;
  const u = localStorage.getItem('pm_user');
  return u ? JSON.parse(u) : null;
};

export const clearAuth = (): void => {
  localStorage.removeItem('pm_token');
  localStorage.removeItem('pm_user');
};

export const isLoggedIn = (): boolean => !!getToken();

// ─── HTTP Helper ──────────────────────────────────────────────────────────────

async function req<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers as Record<string, string> || {}),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearAuth();
    window.location.href = '/login';
    throw new Error('Session expired');
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error((data as { detail?: string }).detail || `Error ${res.status}`);
  return data as T;
}

// ─── Auth API ─────────────────────────────────────────────────────────────────

export const AuthAPI = {
  register: (fullName: string, email: string, password: string) =>
    req<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ full_name: fullName, email, password, role: 'student' }),
    }),

  login: (email: string, password: string) =>
    req<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
};

// ─── Student API ──────────────────────────────────────────────────────────────

export const StudentAPI = {
  getProfile: () => req<{ profile: StudentProfile; user: User }>('/students/me'),
  getRoadmap: () => req<Roadmap>('/students/me/roadmap'),
  getInterviews: () => req<{ interviews: MockInterview[]; total_interviews: number; average_score?: number }>('/students/me/interviews'),
  updateProfile: (data: Partial<StudentProfile>) =>
    req('/students/me/profile', { method: 'PATCH', body: JSON.stringify(data) }),
};

// ─── Chat API ─────────────────────────────────────────────────────────────────

export const ChatAPI = {
  sendMessage: (message: string, extra?: Record<string, unknown>) =>
    req<ChatResponse>('/chat/message', {
      method: 'POST',
      body: JSON.stringify({ message, ...extra }),
    }),

  getHistory: () => req<{ history: Array<{ role: string; content: string }> }>('/chat/history'),

  streamMessage: async (
    message: string,
    onToken: (chunk: string) => void,
    onDone?: (meta?: Record<string, unknown>) => void,
    onError?: (err: string) => void,
    sessionId?: string,
  ) => {
    const token = getToken();
    try {
      const res = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ message, session_id: sessionId }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        for (const line of text.split('\n')) {
          if (!line.startsWith('data: ')) continue;
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === 'token') onToken(event.content);
            else if (event.type === 'done' || event.type === 'meta') onDone?.(event);
            else if (event.type === 'error') onError?.(event.content);
          } catch {}
        }
      }
    } catch (err) {
      onError?.((err as Error).message);
    }
  },
};

// ─── Resume API ───────────────────────────────────────────────────────────────

export const ResumeAPI = {
  upload: async (file: File): Promise<{ version: number; next_step: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const token = getToken();
    const res = await fetch(`${API_BASE}/resume/upload`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Upload failed');
    return data;
  },

  list: () => req<Resume[]>('/resume/list'),
};
