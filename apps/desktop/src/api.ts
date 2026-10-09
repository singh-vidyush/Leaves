const API_ROOT = import.meta.env.VITE_API_ROOT ?? 'http://127.0.0.1:8000/api'

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

export type Dashboard = {
  source_count: number
  document_count: number
  sources: Source[]
  recent_documents: Array<{ title: string; path: string; modified_at: string }>
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
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
}
