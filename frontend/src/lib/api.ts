/**
 * Thin fetch client for the Vex dashboard API.
 * Session cookie is httpOnly; a 401 anywhere means "not authed".
 */

export class UnauthorizedError extends Error {
  constructor() {
    super('unauthorized')
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    credentials: 'same-origin',
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    ...init,
  })
  if (res.status === 401) throw new UnauthorizedError()
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error((data as any)?.error || `HTTP ${res.status}`)
  return data as T
}

// ── Types ─────────────────────────────────────────────────────────────────────

export type Me = { ok: boolean; bot_username: string | null; setup_complete: boolean }

export type Overview = { users: number; blocked: number; groups: number; admins: number }

export type Group = {
  id: number
  telegram_group_id: number
  name: string
  type: string | null
  is_active: boolean
  activated_at: string | null
}

export type BlockedWord = { id: number; word: string }

export type BlockedUser = {
  id: number
  telegram_id: number
  first_name: string
  last_name: string | null
  username: string | null
  blocked_at: string | null
}

export type Endpoint = {
  id: number
  name: string
  provider_type: string
  base_url: string | null
  key_hint: string | null
  model_count: number
}

export type AIModel = {
  id: number
  name: string
  model: string
  provider_type: string
  priority: number
  is_active: boolean
  endpoint_id: number | null
  endpoint_name: string | null
}

export type StatRow = {
  id: number
  provider: string
  date: string
  requests: number
  status: string
  last_used: string
  error: string
  raw_response: string
}

export type StatsData = {
  stats: StatRow[]
  summaries: { label: string; total: number; today: number }[]
}

export type PromptData = {
  has_providers: boolean
  current_rules: string
  default_rules: string
  fixed_prefix: string
  fixed_suffix: string
  debug_channel_id: number | null
  alert_threshold: number
  auto_delete_threshold: number
}

// ── Client ────────────────────────────────────────────────────────────────────

export const api = {
  login: (password: string) =>
    req<{ ok: boolean }>('/login', { method: 'POST', body: JSON.stringify({ password }) }),
  logout: () => req<{ ok: boolean }>('/logout', { method: 'POST' }),
  me: () => req<Me>('/me'),

  overview: () => req<Overview>('/overview'),

  groups: () => req<Group[]>('/groups'),
  addGroup: (telegram_group_id: string, group_name: string) =>
    req<{ ok: boolean; message: string }>('/groups', {
      method: 'POST',
      body: JSON.stringify({ telegram_group_id, group_name }),
    }),
  groupWords: (groupId: number) =>
    req<{ group: { id: number; name: string }; words: BlockedWord[] }>(`/groups/${groupId}/words`),
  addGroupWord: (groupId: number, word: string) =>
    req<{ ok: boolean; message: string }>(`/groups/${groupId}/words`, {
      method: 'POST',
      body: JSON.stringify({ word }),
    }),
  deleteGroupWord: (groupId: number, wordId: number) =>
    req<{ ok: boolean }>(`/groups/${groupId}/words/${wordId}`, { method: 'DELETE' }),

  blockedUsers: () => req<BlockedUser[]>('/users/blocked'),

  endpoints: () => req<Endpoint[]>('/endpoints'),
  addEndpoint: (body: { name: string; provider_type: string; api_key: string; base_url: string }) =>
    req<{ ok: boolean; endpoint: Endpoint }>('/endpoints', { method: 'POST', body: JSON.stringify(body) }),
  updateEndpoint: (id: number, body: { name?: string; api_key?: string; base_url?: string }) =>
    req<{ ok: boolean }>(`/endpoints/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteEndpoint: (id: number) => req<{ ok: boolean }>(`/endpoints/${id}`, { method: 'DELETE' }),
  fetchEndpointModels: (id: number) =>
    req<{ models: string[]; error?: string }>(`/endpoints/${id}/models`),

  models: () => req<AIModel[]>('/models'),
  addModel: (body: { endpoint_id: number; model: string; name?: string; priority?: number }) =>
    req<{ ok: boolean; model: AIModel }>('/models', { method: 'POST', body: JSON.stringify(body) }),
  deleteModel: (id: number) => req<{ ok: boolean }>(`/models/${id}`, { method: 'DELETE' }),
  toggleModel: (id: number) =>
    req<{ ok: boolean; is_active: boolean }>(`/models/${id}/toggle`, { method: 'POST' }),
  reorderModels: (ids: number[]) =>
    req<{ ok: boolean }>('/models/reorder', { method: 'POST', body: JSON.stringify({ ids }) }),

  aiStats: (days = 30) => req<StatsData>(`/ai-stats?days=${days}`),
  deleteAiStat: (id: number) => req<{ ok: boolean }>(`/ai-stats/${id}`, { method: 'DELETE' }),

  prompt: () => req<PromptData>('/prompt'),
  savePrompt: (prompt: string) =>
    req<{ ok: boolean; message: string }>('/prompt', { method: 'POST', body: JSON.stringify({ prompt }) }),
  resetPrompt: () => req<{ ok: boolean; message: string }>('/prompt/reset', { method: 'POST' }),
  saveThresholds: (alert_threshold: number, auto_delete_threshold: number) =>
    req<{ ok: boolean; message: string }>('/thresholds', {
      method: 'POST',
      body: JSON.stringify({ alert_threshold, auto_delete_threshold }),
    }),
  saveDebugChannel: (channel_id: string) =>
    req<{ ok: boolean; message: string }>('/debug-channel', {
      method: 'POST',
      body: JSON.stringify({ channel_id }),
    }),

  logs: (lines = 500) => req<{ content: string }>(`/logs?lines=${lines}`),
}
