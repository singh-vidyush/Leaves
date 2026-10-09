import { invoke, isTauri } from '@tauri-apps/api/core'

const DEFAULT_API_ROOT = import.meta.env.VITE_API_ROOT ?? 'http://127.0.0.1:8000/api'
let resolvedApiRoot: string | null = null

async function getApiRoot(): Promise<string> {
  if (resolvedApiRoot) return resolvedApiRoot
  if (isTauri()) {
    const port = await invoke<number>('backend_api_port')
    const apiRoot = `http://127.0.0.1:${port}/api`
    resolvedApiRoot = apiRoot
    return apiRoot
  }
  resolvedApiRoot = DEFAULT_API_ROOT
  return DEFAULT_API_ROOT
}

export type Source = {
  id: number
  path: string
  recursive: boolean
  created_at: string
  last_indexed_at: string | null
}

export type SearchResult = {
  id: number
  path: string
  title: string
  modified_at: string
  excerpt: string
}

export type TaskItem = {
  id: number
  title: string
  description: string
  source_type: string
  source_ref: string
  urgency_score: number
  urgency_reason: string
  suggested_duration_minutes: number
  deadline: string | null
  status: 'pending' | 'scheduled' | 'completed' | 'dismissed'
  created_at: string
}

export type CalendarEventItem = {
  id: number
  remote_id: string | null
  title: string
  description: string
  start_time: string
  end_time: string
  status: string
  created_by: string
}

export type NotificationItem = {
  id: number
  title: string
  message: string
  event_id: number | null
  task_id: number | null
  is_read: number
  created_at: string
}

export type Dashboard = {
  source_count: number
  document_count: number
  email_count: number
  calendar_count: number
  pending_task_count: number
  unread_notifications: number
  sources: Source[]
  recent_documents: Array<{ title: string; path: string; modified_at: string }>
  upcoming_events: CalendarEventItem[]
  high_priority_tasks: TaskItem[]
}

export type ModelSettings = {
  active_provider: string
  providers: Record<string, { configured: boolean; masked_key: string }>
  supported_providers: string[]
}

export type AvailabilitySettings = {
  working_hours_start: string
  working_hours_end: string
  break_start: string
  break_end: string
  default_duration_minutes: string
  notifications_enabled: string
}

export type TimeAwayBlock = {
  id: number
  title: string
  start_time: string
  end_time: string
  created_at: string
}

export type GoogleConnectionStatus = { gmail: boolean; calendar: boolean }

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${await getApiRoot()}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? `Leaves service returned ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  dashboard: () => request<Dashboard>('/dashboard'),
  sources: () => request<Source[]>('/sources'),
  addSource: (path: string, recursive: boolean) =>
    request<{ id: number; indexed: number }>('/sources', {
      method: 'POST',
      body: JSON.stringify({ path, recursive }),
    }),
  refreshSource: (id: number) => request(`/sources/${id}/refresh`, { method: 'POST' }),
  removeSource: (id: number) => request(`/sources/${id}`, { method: 'DELETE' }),
  search: (query: string) => request<SearchResult[]>(`/search?q=${encodeURIComponent(query)}`),

  // Model & Availability Settings
  modelSettings: () => request<ModelSettings>('/settings/model'),
  updateModelSettings: (payload: { active_provider?: string; provider?: string; api_key?: string }) =>
    request<ModelSettings>('/settings/model', { method: 'POST', body: JSON.stringify(payload) }),
  deleteModelKey: (provider: string) => request<{ deleted: boolean }>(`/settings/model/${provider}`, { method: 'DELETE' }),
  availability: () => request<AvailabilitySettings>('/settings/availability'),
  updateAvailability: (payload: Partial<AvailabilitySettings>) =>
    request<AvailabilitySettings>('/settings/availability', { method: 'POST', body: JSON.stringify(payload) }),
  timeAwayBlocks: () => request<TimeAwayBlock[]>('/settings/time-away'),
  addTimeAwayBlock: (payload: { title: string; start_time: string; end_time: string }) =>
    request<TimeAwayBlock>('/settings/time-away', { method: 'POST', body: JSON.stringify(payload) }),
  removeTimeAwayBlock: (id: number) =>
    request<{ deleted: boolean }>(`/settings/time-away/${id}`, { method: 'DELETE' }),

  googleConnectionStatus: () => request<GoogleConnectionStatus>('/auth/google/status'),
  startGoogleConnection: (service: 'gmail' | 'calendar') =>
    request<{ authorization_url: string; state: string; service: string }>(`/auth/google/${service}/start`, { method: 'POST' }),
  disconnectGoogle: (service: 'gmail' | 'calendar') =>
    request<{ disconnected: boolean }>(`/auth/google/${service}`, { method: 'DELETE' }),

  // Gmail
  syncGmail: (label?: string) =>
    request<{ synced_count: number; mode: 'sample' | 'live' }>(`/integrations/gmail/sync${label ? `?label=${encodeURIComponent(label)}` : ''}`, { method: 'POST' }),
  pollGmailAutomation: () => request<{
    connected: boolean
    baseline: boolean
    new_emails: number
    new_tasks: number
    scheduled_count: number
  }>('/automation/gmail/poll', { method: 'POST' }),
  listGmail: (limit = 50) => request<any[]>(`/integrations/gmail/emails?limit=${limit}`),
  deleteGmail: (id: number) => request<{ deleted: boolean; original_email_deleted: boolean }>(`/integrations/gmail/emails/${id}`, { method: 'DELETE' }),

  // Calendar
  syncCalendar: () => request<{ synced_count: number; mode: 'sample' | 'live' }>('/integrations/calendar/sync', { method: 'POST' }),
  listCalendar: (limit = 50) => request<CalendarEventItem[]>(`/integrations/calendar/events?limit=${limit}`),
  addCalendarEvent: (event: { title: string; start_time: string; end_time: string; description?: string }) =>
    request<CalendarEventItem>('/integrations/calendar/events', { method: 'POST', body: JSON.stringify(event) }),
  moveCalendarEvent: (id: number, start_time: string, end_time: string) =>
    request<CalendarEventItem>(`/integrations/calendar/events/${id}`, { method: 'PUT', body: JSON.stringify({ start_time, end_time }) }),
  deleteCalendarEvent: (id: number, confirmed: boolean) =>
    request<{ deleted: boolean }>(`/integrations/calendar/events/${id}?confirmed=${confirmed}`, { method: 'DELETE' }),

  // Tasks & Scheduling
  extractTasks: () => request<TaskItem[]>('/tasks/extract', { method: 'POST' }),
  listTasks: (status?: string) => request<TaskItem[]>(`/tasks${status ? `?status=${status}` : ''}`),
  updateTaskStatus: (id: number, status: string) =>
    request<TaskItem>(`/tasks/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) }),
  scheduleTask: (id: number) => request<{ task_id: number; event: CalendarEventItem }>(`/tasks/${id}/schedule`, { method: 'POST' }),
  resolveConflicts: () => request<CalendarEventItem[]>('/schedule/resolve-conflicts', { method: 'POST' }),

  // Notifications
  notifications: (unreadOnly = false) => request<NotificationItem[]>(`/notifications?unread_only=${unreadOnly}`),
  markNotificationRead: (id: number) => request<{ read: boolean }>(`/notifications/${id}/read`, { method: 'POST' }),

  // Export
  exportData: () => request<any>('/export'),
}
