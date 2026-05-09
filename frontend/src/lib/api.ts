import { getToken } from './auth';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || `HTTP ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string; token_type: string; expires_in: number }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  analyzeSubscription: (data: { subscription_number: string; tenant_url: string; issue_description?: string }) =>
    request('/analyze/subscription', { method: 'POST', body: JSON.stringify(data) }),

  analyzeOrder: (data: { order_number: string; tenant_url: string; issue_description?: string }) =>
    request('/analyze/order', { method: 'POST', body: JSON.stringify(data) }),

  analyzeOrchestration: (data: { orchestration_id: string; tenant_url: string; issue_description?: string }) =>
    request('/analyze/orchestration', { method: 'POST', body: JSON.stringify(data) }),

  getSessions: () => request<any[]>('/sessions'),

  createSession: (tenant_url: string) =>
    request('/sessions', { method: 'POST', body: JSON.stringify({ tenant_url }) }),

  closeSession: (session_id: string) =>
    request(`/sessions/${session_id}`, { method: 'DELETE' }),

  searchKnowledge: (query: string, module?: string, n_results = 5) =>
    request('/knowledge/search', {
      method: 'POST',
      body: JSON.stringify({ query, module, n_results }),
    }),

  health: () => request<{ status: string; components: Record<string, boolean> }>('/health'),
};
