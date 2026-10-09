import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { isTauri } from '@tauri-apps/api/core'
import { open } from '@tauri-apps/plugin-dialog'
import { openUrl } from '@tauri-apps/plugin-opener'
import {
  ArrowUpRight,
  CalendarDays,
  Check,
  ChevronRight,
  CircleHelp,
  Clock3,
  Download,
  FileText,
  FolderPlus,
  Leaf,
  ListTodo,
  LoaderCircle,
  Moon,
  RefreshCw,
  Search,
  Settings2,
  Sun,
  Trash2,
  X,
} from 'lucide-react'
import {
  api,
  type AvailabilitySettings,
  type CalendarEventItem,
  type Dashboard,
  type GoogleOAuthSettings,
  type ModelSettings,
  type NotificationItem,
  type SearchResult,
  type TaskItem,
  type TimeAwayBlock,
} from './api'

type Page = 'overview' | 'tasks' | 'calendar' | 'search' | 'sources' | 'settings'
type Theme = 'light' | 'dark'

const emptyDashboard: Dashboard = {
  source_count: 0,
  document_count: 0,
  email_count: 0,
  calendar_count: 0,
  pending_task_count: 0,
  unread_notifications: 0,
  sources: [],
  recent_documents: [],
  upcoming_events: [],
  high_priority_tasks: [],
}

function timeGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

function errorMessage(error: unknown, fallback: string) {
  if (error instanceof Error) return error.message
  if (typeof error === 'string') return error
  return fallback
}

function displayDate(date: Date) {
  return new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric' }).format(date)
}

function relativeDate(iso: string) {
  try {
    const diff = (Date.now() - new Date(iso).getTime()) / 1000
    if (diff < 60) return 'Just now'
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
  } catch {
    return iso
  }
}

function formatTime(iso: string) {
  try {
    return new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(new Date(iso))
  } catch {
    return iso
  }
}

export function App() {
  const gmailAutomationRunning = useRef(false)
  const [page, setPage] = useState<Page>('overview')
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('leaves-theme')
    if (saved === 'dark' || saved === 'light') return saved
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })
  const [dashboard, setDashboard] = useState<Dashboard>(emptyDashboard)
  const [serviceReady, setServiceReady] = useState(false)
  const [serviceError, setServiceError] = useState('')
  const [busy, setBusy] = useState(false)
  const [actionMessage, setActionMessage] = useState('')

  // Search state
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState('')

  // Sources state
  const [folderPath, setFolderPath] = useState('')
  const [recursive, setRecursive] = useState(true)

  // Tasks state
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [taskFilter, setTaskFilter] = useState<'all' | 'pending' | 'scheduled' | 'completed'>('all')

  // Calendar state
  const [calendarEvents, setCalendarEvents] = useState<CalendarEventItem[]>([])

  // Settings state
  const [modelSettings, setModelSettings] = useState<ModelSettings | null>(null)
  const [googleOAuthSettings, setGoogleOAuthSettings] = useState<GoogleOAuthSettings | null>(null)
  const [googleOAuthError, setGoogleOAuthError] = useState('')
  const [credentialError, setCredentialError] = useState('')
  const [googleConnections, setGoogleConnections] = useState({ gmail: false, calendar: false })
  const [availability, setAvailability] = useState<AvailabilitySettings | null>(null)
  const [timeAwayBlocks, setTimeAwayBlocks] = useState<TimeAwayBlock[]>([])
  const [timeAwayTitle, setTimeAwayTitle] = useState('')
  const [timeAwayStart, setTimeAwayStart] = useState('')
  const [timeAwayEnd, setTimeAwayEnd] = useState('')
  const [apiKeyInputs, setApiKeyInputs] = useState<Record<string, string>>({})
  const [notifications, setNotifications] = useState<NotificationItem[]>([])

  const refreshDashboard = useCallback(async () => {
    try {
      const data = await api.dashboard()
      setDashboard(data)
      setServiceReady(true)
      setServiceError('')
    } catch {
      setDashboard(emptyDashboard)
      setServiceReady(false)
      setServiceError('Local service is connecting...')
    }
  }, [])

  const loadTasks = useCallback(async () => {
    try {
      const data = await api.listTasks()
      setTasks(data)
    } catch {
      // ignore
    }
  }, [])

  const loadCalendar = useCallback(async () => {
    try {
      const data = await api.listCalendar()
      setCalendarEvents(data)
    } catch {
      // ignore
    }
  }, [])

  const loadSettings = useCallback(async () => {
    try {
      const [a, n, blocks] = await Promise.all([
        api.availability(),
        api.notifications(),
        api.timeAwayBlocks(),
      ])
      setAvailability(a)
      setNotifications(n)
      setTimeAwayBlocks(blocks)
    } catch {
      // ignore
    }
    try {
      setModelSettings(await api.modelSettings())
      setCredentialError('')
    } catch {
      setModelSettings(null)
      setCredentialError('Model settings need an available operating-system credential store.')
    }
    try { setGoogleConnections(await api.googleConnectionStatus()) } catch { /* Secure storage may be unavailable. */ }
    try {
      setGoogleOAuthSettings(await api.googleOAuthSettings())
      setGoogleOAuthError('')
    } catch (error) {
      setGoogleOAuthSettings(null)
      setGoogleOAuthError(errorMessage(error, 'OAuth settings need an available operating-system credential store.'))
    }
  }, [])

  useEffect(() => {
    void refreshDashboard()
    void loadTasks()
    void loadCalendar()
    void loadSettings()
    const interval = window.setInterval(() => {
      void refreshDashboard()
    }, 15_000)
    return () => window.clearInterval(interval)
  }, [refreshDashboard, loadTasks, loadCalendar, loadSettings])

  useEffect(() => {
    const refreshConnections = () => { void api.googleConnectionStatus().then(setGoogleConnections).catch(() => undefined) }
    window.addEventListener('focus', refreshConnections)
    return () => window.removeEventListener('focus', refreshConnections)
  }, [])

  useEffect(() => {
    let active = true
    const pollGmail = async () => {
      if (gmailAutomationRunning.current) return
      gmailAutomationRunning.current = true
      try {
        const result = await api.pollGmailAutomation()
        if (!active || !result.connected || result.baseline) return
        if (result.new_emails > 0) await refreshDashboard()
        if (result.scheduled_count > 0) {
          setActionMessage(`Automatically scheduled ${result.scheduled_count} urgent email task${result.scheduled_count === 1 ? '' : 's'}.`)
          await Promise.all([loadTasks(), loadCalendar(), refreshDashboard()])
        }
      } catch {
        // Gmail automation retries on the next interval or when the app regains focus.
      } finally {
        gmailAutomationRunning.current = false
      }
    }
    const onFocus = () => { void pollGmail() }
    void pollGmail()
    const interval = window.setInterval(() => { void pollGmail() }, 5 * 60 * 1000)
    window.addEventListener('focus', onFocus)
    return () => {
      active = false
      window.clearInterval(interval)
      window.removeEventListener('focus', onFocus)
    }
  }, [loadTasks, loadCalendar, refreshDashboard])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('leaves-theme', theme)
  }, [theme])

  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setPage('search')
        window.setTimeout(() => document.getElementById('main-search-input')?.focus(), 0)
      }
    }
    window.addEventListener('keydown', handleShortcut)
    return () => window.removeEventListener('keydown', handleShortcut)
  }, [])

  const dateText = useMemo(() => displayDate(new Date()), [])

  async function runSearch(event?: FormEvent) {
    event?.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) {
      setSearchResults([])
      return
    }
    setPage('search')
    setSearching(true)
    setSearchError('')
    try {
      setSearchResults(await api.search(trimmed))
    } catch (error) {
      setSearchError(error instanceof Error ? error.message : 'Search error')
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }

  async function selectFolder() {
    if (isTauri()) {
      try {
        const picked = await open({ directory: true, multiple: false })
        if (typeof picked === 'string') {
          setFolderPath(picked)
          await addFolder(picked)
        }
      } catch {
        // fallback
      }
    } else {
      const manual = window.prompt('Enter full folder path to index:', folderPath || '/Users/vidyushsingh/Notes')
      if (manual) {
        setFolderPath(manual)
        await addFolder(manual)
      }
    }
  }

  async function addFolder(targetPath = folderPath) {
    if (!targetPath.trim()) return
    setBusy(true)
    setActionMessage('Scanning folder...')
    try {
      const res = await api.addSource(targetPath.trim(), recursive)
      setActionMessage(`Indexed ${res.indexed} notes`)
      setFolderPath('')
      await refreshDashboard()
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Could not add folder')
    } finally {
      setBusy(false)
    }
  }

  async function refreshSource(id: number) {
    setBusy(true)
    setActionMessage('Refreshing index...')
    try {
      await api.refreshSource(id)
      setActionMessage('Source refreshed')
      await refreshDashboard()
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Refresh failed')
    } finally {
      setBusy(false)
    }
  }

  async function removeSource(id: number) {
    if (!window.confirm('Remove this folder from Leaves index? (Original files are never touched)')) return
    setBusy(true)
    try {
      await api.removeSource(id)
      setActionMessage('Folder removed from index')
      await refreshDashboard()
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Could not remove folder')
    } finally {
      setBusy(false)
    }
  }

  async function handleExtractTasks() {
    setBusy(true)
    setActionMessage('Extracting tasks & analyzing urgency...')
    try {
      const extracted = await api.extractTasks()
      setActionMessage(`Extracted ${extracted.length} tasks with explainable urgency`)
      await loadTasks()
      await refreshDashboard()
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Extraction error')
    } finally {
      setBusy(false)
    }
  }

  async function handleScheduleTask(taskId: number) {
    setBusy(true)
    setActionMessage('Scheduling task within availability windows...')
    try {
      await api.scheduleTask(taskId)
      setActionMessage('Task scheduled into calendar!')
      await loadTasks()
      await loadCalendar()
      await refreshDashboard()
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Scheduling error')
    } finally {
      setBusy(false)
    }
  }

  async function handleSyncGmail() {
    setBusy(true)
    setActionMessage('Syncing Gmail...')
    try {
      const res = await api.syncGmail()
      setActionMessage(`Synced ${res.synced_count} ${res.mode === 'live' ? 'Gmail' : 'sample'} emails.`)
      await refreshDashboard()
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Gmail sync error')
    } finally {
      setBusy(false)
    }
  }

  async function handleSyncCalendar() {
    setBusy(true)
    setActionMessage('Syncing calendar...')
    try {
      const res = await api.syncCalendar()
      setActionMessage(`Synced ${res.synced_count} ${res.mode === 'live' ? 'Google Calendar' : 'sample calendar'} events.`)
      await loadCalendar()
      await refreshDashboard()
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Calendar sync error')
    } finally {
      setBusy(false)
    }
  }

  async function handleGoogleConnection(service: 'gmail' | 'calendar') {
    setBusy(true)
    try {
      let authorizationUrl: string
      try {
        ({ authorization_url: authorizationUrl } = await api.startGoogleConnection(service))
      } catch (error) {
        setActionMessage(errorMessage(error, 'Leaves could not create the Google authorization request.'))
        return
      }

      if (isTauri()) {
        try {
          await openUrl(authorizationUrl)
        } catch {
          setActionMessage('Leaves created the Google sign-in request, but could not open your browser.')
          return
        }
      } else {
        const browserWindow = window.open(authorizationUrl, '_blank', 'noopener,noreferrer')
        if (!browserWindow) {
          setActionMessage('Your browser blocked the Google sign-in window. Allow pop-ups and try again.')
          return
        }
      }
      setActionMessage(`Finish Google ${service} authorization in your browser, then return to Leaves.`)
    } finally {
      setBusy(false)
    }
  }

  async function handleGoogleDisconnect(service: 'gmail' | 'calendar') {
    setBusy(true)
    try {
      await api.disconnectGoogle(service)
      setGoogleConnections(await api.googleConnectionStatus())
      setActionMessage(`Google ${service} disconnected.`)
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Could not disconnect Google')
    } finally {
      setBusy(false)
    }
  }

  async function handleResolveConflicts() {
    setBusy(true)
    setActionMessage('Resolving schedule conflicts...')
    try {
      const moved = await api.resolveConflicts()
      setActionMessage(moved.length ? `Rescheduled ${moved.length} events to avoid conflicts` : 'No conflicts found!')
      await loadCalendar()
      await refreshDashboard()
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Conflict resolution error')
    } finally {
      setBusy(false)
    }
  }

  async function handleDeleteCalendarEvent(eventId: number) {
    // NON-NEGOTIABLE: Deleting calendar events always requires explicit user approval
    const ok = window.confirm('Approval Required: Deleting calendar events requires explicit user confirmation. Do you approve deleting this event?')
    if (!ok) return

    setBusy(true)
    try {
      await api.deleteCalendarEvent(eventId, true)
      setActionMessage('Calendar event deleted')
      await loadCalendar()
      await refreshDashboard()
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Could not delete event')
    } finally {
      setBusy(false)
    }
  }

  async function handleSaveModelConfig(activeProvider: string) {
    setBusy(true)
    try {
      const key = apiKeyInputs[activeProvider]
      await api.updateModelSettings({
        active_provider: activeProvider,
        provider: key ? activeProvider : undefined,
        api_key: key || undefined,
      })
      setActionMessage(`Active provider set to ${activeProvider}`)
      setApiKeyInputs((prev) => ({ ...prev, [activeProvider]: '' }))
      await loadSettings()
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Failed to update model settings')
    } finally {
      setBusy(false)
    }
  }

  async function handleSaveGoogleOAuthSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const values = new FormData(form)
    const clientId = String(values.get('google-client-id') ?? '').trim()
    const clientSecret = String(values.get('google-client-secret') ?? '').trim()
    if (!clientId && !clientSecret) {
      setGoogleOAuthError('Enter a Client ID or Client Secret to save.')
      return
    }

    setBusy(true)
    setGoogleOAuthError('')
    try {
      const settings = await api.saveGoogleOAuthSettings({
        client_id: clientId || undefined,
        client_secret: clientSecret || undefined,
      })
      setGoogleOAuthSettings(settings)
      form.reset()
      setActionMessage(settings.ready
        ? 'Google OAuth credentials saved securely in Keychain.'
        : 'Saved. Enter the remaining Google OAuth credential to connect an account.')
    } catch (error) {
      setGoogleOAuthError(errorMessage(error, 'Could not save Google OAuth credentials.'))
    } finally {
      setBusy(false)
    }
  }

  async function handleRemoveGoogleOAuthSettings() {
    if (!window.confirm('Remove the Google OAuth Client ID and Secret? This will also disconnect Gmail and Google Calendar.')) return
    setBusy(true)
    setGoogleOAuthError('')
    try {
      setGoogleOAuthSettings(await api.removeGoogleOAuthSettings())
      setGoogleConnections(await api.googleConnectionStatus())
      setActionMessage('Google OAuth credentials removed from Keychain.')
    } catch (error) {
      setGoogleOAuthError(errorMessage(error, 'Could not remove Google OAuth credentials.'))
    } finally {
      setBusy(false)
    }
  }

  async function handleExport() {
    setBusy(true)
    try {
      const data = await api.exportData()
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `leaves-export-${new Date().toISOString().split('T')[0]}.json`
      a.click()
      URL.revokeObjectURL(url)
      setActionMessage('Local data exported successfully')
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setBusy(false)
    }
  }

  async function handleAddTimeAway(event: FormEvent) {
    event.preventDefault()
    if (!timeAwayTitle.trim() || !timeAwayStart || !timeAwayEnd) return
    setBusy(true)
    try {
      await api.addTimeAwayBlock({
        title: timeAwayTitle.trim(),
        start_time: new Date(timeAwayStart).toISOString(),
        end_time: new Date(timeAwayEnd).toISOString(),
      })
      setTimeAwayTitle('')
      setTimeAwayStart('')
      setTimeAwayEnd('')
      setTimeAwayBlocks(await api.timeAwayBlocks())
      setActionMessage('Time away added to your scheduling constraints')
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Could not add time away')
    } finally {
      setBusy(false)
    }
  }

  async function handleRemoveTimeAway(blockId: number) {
    try {
      await api.removeTimeAwayBlock(blockId)
      setTimeAwayBlocks(await api.timeAwayBlocks())
      setActionMessage('Time away removed')
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : 'Could not remove time away')
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <span className="brand-badge"><Leaf size={15} /></span>
          <div className="brand-text">
            <span className="brand-name">Leaves</span>
            <span className="workspace-label">Local-first Agent</span>
          </div>
        </div>

        <nav className="nav-group">
          <button className={`nav-item ${page === 'overview' ? 'active' : ''}`} onClick={() => setPage('overview')}>
            <Leaf size={17} /><span>Overview</span>
          </button>
          <button className={`nav-item ${page === 'tasks' ? 'active' : ''}`} onClick={() => setPage('tasks')}>
            <ListTodo size={17} /><span>Tasks & Urgency</span>
            {dashboard.pending_task_count > 0 && <span className="section-count">{dashboard.pending_task_count}</span>}
          </button>
          <button className={`nav-item ${page === 'calendar' ? 'active' : ''}`} onClick={() => setPage('calendar')}>
            <CalendarDays size={17} /><span>Calendar</span>
            {dashboard.calendar_count > 0 && <span className="section-count">{dashboard.calendar_count}</span>}
          </button>
          <button className={`nav-item ${page === 'search' ? 'active' : ''}`} onClick={() => setPage('search')}>
            <Search size={17} /><span>Search</span><kbd>⌘ K</kbd>
          </button>
          <button className={`nav-item ${page === 'sources' ? 'active' : ''}`} onClick={() => setPage('sources')}>
            <FolderPlus size={17} /><span>Sources</span>
          </button>
          <button className={`nav-item ${page === 'settings' ? 'active' : ''}`} onClick={() => setPage('settings')}>
            <Settings2 size={17} /><span>Settings</span>
          </button>
        </nav>

        <div className="sidebar-section-head">
          <span>CONNECTED</span><span className="section-count">{dashboard.source_count}</span>
        </div>
        <div className="connected-list">
          {dashboard.sources.length ? (
            dashboard.sources.map((source) => (
              <button key={source.id} className="connected-source" onClick={() => setPage('sources')} title={source.path}>
                <span className="source-dot markdown-dot"><FileText size={13} /></span>
                <span className="source-name">{source.path.split('/').filter(Boolean).at(-1) ?? source.path}</span>
                <span className="source-online" />
              </button>
            ))
          ) : (
            <div className="sidebar-empty">Add notes or connect Gmail</div>
          )}
        </div>

        <div className="sidebar-bottom">
          <div className="local-note"><span className="local-pulse" /> Stored on this device</div>
          <button className="nav-item settings-link" onClick={() => setPage('settings')}>
            <Settings2 size={17} /><span>Settings & Keys</span>
          </button>
          <div className="profile-row">
            <div className="profile-avatar">L</div>
            <div className="profile-copy">
              <strong>Leaves</strong>
              <span>Personal workspace</span>
            </div>
            <button className="icon-button small" onClick={() => setPage('settings')} aria-label="Settings" title="Settings">
              <CircleHelp size={16} />
            </button>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumbs">
            <span>Leaves</span><ChevronRight size={14} />
            <strong>{page.toUpperCase()}</strong>
          </div>
          <div className="topbar-right">
            {actionMessage && <span style={{ fontSize: '13px', color: 'var(--accent)', fontWeight: 500 }}>{actionMessage}</span>}
            <span className={`service-state ${serviceReady ? 'online' : 'offline'}`}>
              <span />{serviceReady ? 'Local and ready' : 'Connecting'}
            </span>
            <button
              className="icon-button theme-button"
              onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
              aria-label="Toggle theme"
            >
              {theme === 'light' ? <Moon size={17} /> : <Sun size={17} />}
            </button>
          </div>
        </header>

        {serviceError && (
          <div className="service-banner">
            <span>{serviceError}</span>
          </div>
        )}

        {/* OVERVIEW PAGE */}
        {page === 'overview' && (
          <div className="page-content overview-page">
            <div className="welcome-row">
              <div>
                <div className="eyebrow"><span className="eyebrow-line" />{dateText}</div>
                <h1>{timeGreeting()}<span className="title-comma">,</span> take a breath.</h1>
                <p className="welcome-subtitle">Local agent scheduling your day with explainable priorities.</p>
              </div>
              <div className="sun-stamp" aria-hidden="true"><span>葉</span><i /></div>
            </div>

            <form
              className="hero-search"
              onSubmit={(e) => {
                e.preventDefault()
                const val = (new FormData(e.currentTarget).get('q') as string) || ''
                setQuery(val)
                setPage('search')
                void api.search(val).then(setSearchResults)
              }}
            >
              <Search size={20} />
              <input id="main-search-input" name="q" placeholder="Search your notes, emails, and plans…" />
              <kbd>⌘ K</kbd>
              <button className="search-arrow" aria-label="Search"><ArrowUpRight size={19} /></button>
            </form>

            <div className="overview-grid">
              {/* Day / Schedule Panel */}
              <section className="panel day-panel">
                <div className="panel-heading">
                  <div><div className="eyebrow muted-eyebrow">YOUR DAY</div><h2>Schedule</h2></div>
                  <button className="text-button" onClick={() => void handleResolveConflicts()} disabled={busy}>
                    Resolve conflicts <RefreshCw size={13} />
                  </button>
                </div>

                {dashboard.upcoming_events && dashboard.upcoming_events.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '12px 0' }}>
                    {dashboard.upcoming_events.map((evt) => (
                      <div
                        key={evt.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          padding: '10px 14px',
                          background: 'var(--panel)',
                          border: '1px solid var(--line)',
                          borderRadius: '8px',
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: 600 }}>{evt.title}</div>
                          <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
                            {formatTime(evt.start_time)} – {formatTime(evt.end_time)} ({evt.created_by})
                          </div>
                        </div>
                        <button
                          className="icon-button small"
                          onClick={() => void handleDeleteCalendarEvent(evt.id)}
                          title="Delete event (requires approval)"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="schedule-empty">
                    <div className="schedule-art">
                      <span className="schedule-leaf"><Leaf size={25} /></span>
                    </div>
                    <h3>No scheduled commitments yet</h3>
                    <p>Sync your Google Calendar or let Leaves extract and schedule your tasks.</p>
                    <button className="text-button" onClick={() => void handleSyncCalendar()}>
                      Sync calendar <ArrowUpRight size={15} />
                    </button>
                  </div>
                )}
                <div className="day-footer">
                  <span><Clock3 size={14} /> Local urgency-aware planner</span>
                  <span className="planned-badge">ACTIVE</span>
                </div>
              </section>

              {/* Tasks / Urgency Panel */}
              <section className="panel sources-panel">
                <div className="panel-heading">
                  <div><div className="eyebrow muted-eyebrow">PRIORITY TASKS</div><h2>Explainable Urgency</h2></div>
                  <button className="text-button" onClick={() => void handleExtractTasks()} disabled={busy}>
                    Extract tasks <ArrowUpRight size={14} />
                  </button>
                </div>
                <div className="stat-pair">
                  <div className="stat-card">
                    <span>Pending tasks</span>
                    <strong>{dashboard.pending_task_count.toString().padStart(2, '0')}</strong>
                    <small>ranked by urgency</small>
                  </div>
                  <div className="stat-card">
                    <span>Calendar events</span>
                    <strong>{dashboard.calendar_count.toString().padStart(2, '0')}</strong>
                    <small>in local store</small>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '12px' }}>
                  {dashboard.high_priority_tasks && dashboard.high_priority_tasks.length > 0 ? (
                    dashboard.high_priority_tasks.map((t) => (
                      <div
                        key={t.id}
                        style={{
                          padding: '10px 12px',
                          background: 'var(--sidebar)',
                          borderRadius: '8px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                        }}
                      >
                        <div style={{ maxWidth: '75%' }}>
                          <div style={{ fontWeight: 600, fontSize: '13px' }}>{t.title}</div>
                          <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                            Urgency {t.urgency_score}/10: {t.urgency_reason}
                          </div>
                        </div>
                        <button
                          className="text-button"
                          style={{ fontSize: '12px', padding: '4px 8px' }}
                          onClick={() => void handleScheduleTask(t.id)}
                          disabled={busy}
                        >
                          Schedule
                        </button>
                      </div>
                    ))
                  ) : (
                    <div style={{ fontSize: '13px', color: 'var(--muted)', padding: '12px 0' }}>
                      No tasks extracted yet. Click "Extract tasks" above!
                    </div>
                  )}
                </div>
                <button className="panel-link" onClick={() => setPage('tasks')}>
                  View all tasks & urgency <ChevronRight size={15} />
                </button>
              </section>
            </div>
          </div>
        )}

        {/* TASKS PAGE */}
        {page === 'tasks' && (
          <div className="page-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <h2>Extracted Tasks & Urgency Ranking</h2>
                <p style={{ color: 'var(--muted)', fontSize: '14px', margin: '4px 0 0' }}>
                  Extracted from permitted Markdown notes and task-relevant emails. Urgency is explainable.
                </p>
              </div>
              <button
                className="text-button"
                style={{ padding: '8px 16px', background: 'var(--accent)', color: '#fff', borderRadius: '6px' }}
                onClick={() => void handleExtractTasks()}
                disabled={busy}
              >
                {busy ? <LoaderCircle size={15} className="spinner" /> : <RefreshCw size={15} />} Extract & Re-score
              </button>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
              {(['all', 'pending', 'scheduled', 'completed'] as const).map((tab) => (
                <button
                  key={tab}
                  className={`nav-item ${taskFilter === tab ? 'active' : ''}`}
                  style={{ width: 'auto', padding: '6px 12px', borderRadius: '6px' }}
                  onClick={() => setTaskFilter(tab)}
                >
                  {tab.toUpperCase()}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {tasks
                .filter((t) => taskFilter === 'all' || t.status === taskFilter)
                .map((t) => (
                  <div
                    key={t.id}
                    style={{
                      padding: '16px',
                      background: 'var(--panel)',
                      border: '1px solid var(--line)',
                      borderRadius: '8px',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span
                          style={{
                            fontSize: '11px',
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: '12px',
                            background: t.urgency_score >= 8 ? 'var(--accent-soft)' : 'var(--green-soft)',
                            color: t.urgency_score >= 8 ? 'var(--accent)' : 'var(--green)',
                          }}
                        >
                          Urgency {t.urgency_score}/10
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase' }}>
                          {t.source_type} ({t.status})
                        </span>
                        {t.deadline && (
                          <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
                            Due: {formatTime(t.deadline)}
                          </span>
                        )}
                      </div>
                      <div style={{ fontWeight: 600, fontSize: '15px', marginTop: '6px' }}>{t.title}</div>
                      <div style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '2px' }}>
                        {t.urgency_reason} • Estimated {t.suggested_duration_minutes} min
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      {t.status === 'pending' && (
                        <button
                          className="text-button"
                          style={{ padding: '6px 12px', background: 'var(--green)', color: '#fff', borderRadius: '4px' }}
                          onClick={() => void handleScheduleTask(t.id)}
                          disabled={busy}
                        >
                          Schedule
                        </button>
                      )}
                      <button
                        className="text-button"
                        style={{ padding: '6px 10px', fontSize: '12px' }}
                        onClick={() => void api.updateTaskStatus(t.id, 'completed').then(() => loadTasks())}
                      >
                        <Check size={14} /> Done
                      </button>
                    </div>
                  </div>
                ))}
              {tasks.length === 0 && (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--muted)' }}>
                  No tasks extracted yet. Click "Extract & Re-score" to analyze your connected notes and emails.
                </div>
              )}
            </div>
          </div>
        )}

        {/* CALENDAR PAGE */}
        {page === 'calendar' && (
          <div className="page-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <h2>Google Calendar & Local Commitments</h2>
                <p style={{ color: 'var(--muted)', fontSize: '14px', margin: '4px 0 0' }}>
                  Leaves arranges tasks around your commitments and availability. Deleting events always requires user approval.
                </p>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button className="text-button" onClick={() => void handleSyncCalendar()} disabled={busy}>
                  Sync calendar <RefreshCw size={13} />
                </button>
                <button className="text-button" onClick={() => void handleResolveConflicts()} disabled={busy}>
                  Resolve conflicts
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {calendarEvents.map((evt) => (
                <div
                  key={evt.id}
                  style={{
                    padding: '14px 16px',
                    background: 'var(--panel)',
                    border: '1px solid var(--line)',
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '15px' }}>{evt.title}</div>
                    <div style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '2px' }}>
                      {formatTime(evt.start_time)} – {formatTime(evt.end_time)} • Created by {evt.created_by}
                    </div>
                    {evt.description && (
                      <div style={{ fontSize: '12px', color: 'var(--subtle)', marginTop: '4px' }}>
                        {evt.description}
                      </div>
                    )}
                  </div>
                  <button
                    className="icon-button"
                    onClick={() => void handleDeleteCalendarEvent(evt.id)}
                    title="Delete event (requires approval)"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
              {calendarEvents.length === 0 && (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--muted)' }}>
                  No calendar commitments found. Sync Google Calendar or load sample data to explore scheduling.
                </div>
              )}
            </div>
          </div>
        )}

        {/* SEARCH PAGE */}
        {page === 'search' && (
          <div className="page-content">
            <h2>Full-Text Search</h2>
            <form onSubmit={runSearch} style={{ display: 'flex', gap: '8px', margin: '16px 0 24px' }}>
              <input
                style={{ flex: 1, padding: '10px 14px', borderRadius: '6px', border: '1px solid var(--line)', background: 'var(--panel)' }}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search notes, documents, and context..."
              />
              <button className="text-button" type="submit" disabled={searching}>
                {searching ? 'Searching...' : 'Search'}
              </button>
            </form>
            {searchError && <div style={{ color: 'var(--accent)', marginBottom: '12px' }}>{searchError}</div>}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {searchResults.map((r) => (
                <div key={r.id} style={{ padding: '14px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: '8px' }}>
                  <div style={{ fontWeight: 600 }}>{r.title}</div>
                  <div style={{ fontSize: '12px', color: 'var(--muted)', margin: '4px 0' }}>{r.path}</div>
                  <div style={{ fontSize: '13px', color: 'var(--ink)' }}>{r.excerpt}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SOURCES PAGE */}
        {page === 'sources' && (
          <div className="page-content">
            <h2>Connected Context Sources</h2>
            <p style={{ color: 'var(--muted)', fontSize: '14px', margin: '4px 0 20px' }}>
              Manage local Markdown folders and connect Google services with read-only Gmail and event access.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
              {/* Folder Picker Card */}
              <div style={{ padding: '16px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: '8px' }}>
                <h3>Local Markdown Folders</h3>
                <p style={{ fontSize: '13px', color: 'var(--muted)' }}>Select local folders containing notes to index.</p>
                <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                  <button className="text-button" onClick={() => void selectFolder()} disabled={busy}>
                    Choose Folder <FolderPlus size={14} />
                  </button>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}>
                    <input type="checkbox" checked={recursive} onChange={(e) => setRecursive(e.target.checked)} />
                    Recursive
                  </label>
                </div>
              </div>

              {/* Gmail Sync Card */}
              <div style={{ padding: '16px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: '8px' }}>
                <h3>Gmail {googleConnections.gmail ? 'Connected' : 'Not connected'}</h3>
                <p style={{ fontSize: '13px', color: 'var(--muted)' }}>
                  Reads Gmail messages for task extraction. Email text sent to an AI provider is limited to relevant excerpts.
                </p>
                <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                  <button className="text-button" onClick={() => void (googleConnections.gmail ? handleGoogleDisconnect('gmail') : handleGoogleConnection('gmail'))} disabled={busy}>
                    {googleConnections.gmail ? 'Disconnect Gmail' : 'Connect Gmail'}
                  </button>
                  <button className="text-button" onClick={() => void handleSyncGmail()} disabled={busy}>
                    Sync email <RefreshCw size={14} />
                  </button>
                </div>
              </div>

              <div style={{ padding: '16px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: '8px' }}>
                <h3>Google Calendar {googleConnections.calendar ? 'Connected' : 'Not connected'}</h3>
                <p style={{ fontSize: '13px', color: 'var(--muted)' }}>
                  Reads event times and writes events created by Leaves. Event titles and descriptions remain on this device.
                </p>
                <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                  <button className="text-button" onClick={() => void (googleConnections.calendar ? handleGoogleDisconnect('calendar') : handleGoogleConnection('calendar'))} disabled={busy}>
                    {googleConnections.calendar ? 'Disconnect Calendar' : 'Connect Calendar'}
                  </button>
                  <button className="text-button" onClick={() => void handleSyncCalendar()} disabled={busy}>
                    Sync calendar <RefreshCw size={14} />
                  </button>
                </div>
              </div>
            </div>

            <h3>Indexed Folders ({dashboard.sources.length})</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '8px' }}>
              {dashboard.sources.map((s) => (
                <div
                  key={s.id}
                  style={{
                    padding: '12px',
                    background: 'var(--panel)',
                    border: '1px solid var(--line)',
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600 }}>{s.path}</div>
                    <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
                      Recursive: {s.recursive ? 'Yes' : 'No'} • Last indexed: {s.last_indexed_at ? relativeDate(s.last_indexed_at) : 'Never'}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="icon-button" onClick={() => void refreshSource(s.id)} title="Refresh">
                      <RefreshCw size={15} />
                    </button>
                    <button className="icon-button" onClick={() => void removeSource(s.id)} title="Remove index">
                      <X size={15} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* SETTINGS PAGE */}
        {page === 'settings' && (
          <div className="page-content">
            <h2>Settings</h2>
            <p style={{ color: 'var(--muted)', fontSize: '14px', margin: '4px 0 20px' }}>
              OAuth and model credentials are stored securely in macOS Keychain, outside project files and the local database.
            </p>

            <div style={{ padding: '18px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: '8px', marginBottom: '20px' }}>
              <h3>Google OAuth</h3>
              <p style={{ fontSize: '13px', color: 'var(--muted)' }}>
                Enter the Client ID and Client Secret from the same Google OAuth Desktop client. Values are saved to Keychain and never shown again.
              </p>
              <p role="status" style={{ fontSize: '13px', color: googleOAuthSettings?.ready ? 'var(--success, var(--ink))' : 'var(--muted)' }}>
                {googleOAuthSettings?.ready
                  ? 'OAuth credentials are ready.'
                  : googleOAuthSettings
                    ? `Needs ${googleOAuthSettings.client_id_configured ? 'Client Secret' : googleOAuthSettings.client_secret_configured ? 'Client ID' : 'Client ID and Client Secret'}.`
                    : 'Checking secure credential storage…'}
                {' '}Gmail: {googleConnections.gmail ? 'Connected' : 'Not connected'} · Calendar: {googleConnections.calendar ? 'Connected' : 'Not connected'}
              </p>
              {googleOAuthError && <p role="alert" style={{ fontSize: '13px', color: 'var(--accent)' }}>{googleOAuthError}</p>}
              <form onSubmit={(event) => void handleSaveGoogleOAuthSettings(event)} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '10px', alignItems: 'end', marginTop: '14px' }}>
                <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: 'var(--muted)' }}>
                  Google OAuth Client ID
                  <input
                    name="google-client-id"
                    type="password"
                    autoComplete="off"
                    autoCapitalize="none"
                    spellCheck={false}
                    placeholder={googleOAuthSettings?.client_id_configured ? 'Saved in Keychain — blank keeps current value' : 'Paste Client ID'}
                    aria-label="Google OAuth Client ID"
                    style={{ padding: '9px', borderRadius: '4px', border: '1px solid var(--line)', background: 'var(--sidebar)' }}
                  />
                </label>
                <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: 'var(--muted)' }}>
                  Google OAuth Client Secret
                  <input
                    name="google-client-secret"
                    type="password"
                    autoComplete="new-password"
                    placeholder={googleOAuthSettings?.client_secret_configured ? 'Saved in Keychain — blank keeps current value' : 'Paste Client Secret'}
                    aria-label="Google OAuth Client Secret"
                    style={{ padding: '9px', borderRadius: '4px', border: '1px solid var(--line)', background: 'var(--sidebar)' }}
                  />
                </label>
                <button className="text-button" type="submit" disabled={busy}>Save Credentials</button>
              </form>
              <button
                className="text-button"
                style={{ marginTop: '10px' }}
                onClick={() => void handleRemoveGoogleOAuthSettings()}
                disabled={busy || !(googleOAuthSettings?.client_id_configured || googleOAuthSettings?.client_secret_configured)}
              >
                Remove Google Credentials
              </button>
            </div>

            {/* Model Provider Section */}
            <div style={{ padding: '18px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: '8px', marginBottom: '20px' }}>
              <h3>Active LLM Provider</h3>
              <p style={{ fontSize: '13px', color: 'var(--muted)' }}>
                Leaves sends relevant Markdown and email excerpts to your active provider. Calendar event text stays on this device.
              </p>
              {credentialError && <p role="status" style={{ fontSize: '13px', color: 'var(--accent)' }}>{credentialError}</p>}
              <div style={{ display: 'flex', gap: '10px', margin: '14px 0' }}>
                {['heuristic', 'openai', 'anthropic', 'gemini'].map((p) => (
                  <button
                    key={p}
                    className={`nav-item ${modelSettings?.active_provider === p ? 'active' : ''}`}
                    style={{ width: 'auto', padding: '8px 14px', borderRadius: '6px' }}
                    onClick={() => void handleSaveModelConfig(p)}
                    disabled={busy}
                  >
                    {p.toUpperCase()}
                  </button>
                ))}
              </div>

              {modelSettings && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
                  {(['openai', 'anthropic', 'gemini'] as const).map((prov) => (
                    <div key={prov} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ width: '100px', fontWeight: 600, textTransform: 'capitalize' }}>{prov} Key:</span>
                      <input
                        type="password"
                        placeholder={modelSettings.providers[prov]?.masked_key || 'Enter API Key'}
                        value={apiKeyInputs[prov] || ''}
                        onChange={(e) => setApiKeyInputs({ ...apiKeyInputs, [prov]: e.target.value })}
                        style={{ flex: 1, padding: '8px', borderRadius: '4px', border: '1px solid var(--line)', background: 'var(--sidebar)' }}
                      />
                      <button
                        className="text-button"
                        onClick={() => void handleSaveModelConfig(prov)}
                        disabled={!apiKeyInputs[prov]}
                      >
                        Save Key
                      </button>
                      {modelSettings.providers[prov]?.configured && (
                        <button
                          className="icon-button"
                          onClick={() => void api.deleteModelKey(prov).then(() => loadSettings())}
                          title="Delete Key"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Availability Settings */}
            <div style={{ padding: '18px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: '8px', marginBottom: '20px' }}>
              <h3>Availability & Working Hours</h3>
              <p style={{ fontSize: '13px', color: 'var(--muted)' }}>
                Configure daily working hours, break windows, and task duration defaults.
              </p>
              {availability && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '14px' }}>
                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--muted)' }}>Work Hours Start</label>
                    <input
                      style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--line)' }}
                      value={availability.working_hours_start}
                      onChange={(e) => setAvailability({ ...availability, working_hours_start: e.target.value })}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--muted)' }}>Work Hours End</label>
                    <input
                      style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--line)' }}
                      value={availability.working_hours_end}
                      onChange={(e) => setAvailability({ ...availability, working_hours_end: e.target.value })}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--muted)' }}>Break Start</label>
                    <input
                      style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--line)' }}
                      value={availability.break_start}
                      onChange={(e) => setAvailability({ ...availability, break_start: e.target.value })}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: '12px', color: 'var(--muted)' }}>Break End</label>
                    <input
                      style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--line)' }}
                      value={availability.break_end}
                      onChange={(e) => setAvailability({ ...availability, break_end: e.target.value })}
                    />
                  </div>
                  <div style={{ gridColumn: 'span 2' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
                      <input
                        type="checkbox"
                        checked={availability.notifications_enabled === 'true'}
                        onChange={(e) => setAvailability({ ...availability, notifications_enabled: String(e.target.checked) })}
                      />
                      Show schedule update notifications
                    </label>
                  </div>
                  <div style={{ gridColumn: 'span 2' }}>
                    <button
                      className="text-button"
                      onClick={() => void api.updateAvailability(availability).then(() => setActionMessage('Availability updated'))}
                    >
                      Save Availability Settings
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div style={{ padding: '18px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: '8px', marginBottom: '20px' }}>
              <h3>Time Away</h3>
              <p style={{ fontSize: '13px', color: 'var(--muted)' }}>
                Add personal blocks that Leaves will keep clear when scheduling tasks.
              </p>
              <form onSubmit={(event) => void handleAddTimeAway(event)} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '8px', margin: '14px 0' }}>
                <input aria-label="Time away title" placeholder="Title" maxLength={120} value={timeAwayTitle} onChange={(e) => setTimeAwayTitle(e.target.value)} required />
                <input aria-label="Time away starts" type="datetime-local" value={timeAwayStart} onChange={(e) => setTimeAwayStart(e.target.value)} required />
                <input aria-label="Time away ends" type="datetime-local" value={timeAwayEnd} onChange={(e) => setTimeAwayEnd(e.target.value)} required />
                <button className="text-button" type="submit" disabled={busy}>Add block</button>
              </form>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {timeAwayBlocks.map((block) => (
                  <div key={block.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', background: 'var(--sidebar)', borderRadius: '6px' }}>
                    <span>{block.title} · {new Date(block.start_time).toLocaleString()} – {new Date(block.end_time).toLocaleString()}</span>
                    <button className="icon-button" onClick={() => void handleRemoveTimeAway(block.id)} aria-label={`Remove ${block.title}`} title="Remove time-away block"><Trash2 size={14} /></button>
                  </div>
                ))}
                {timeAwayBlocks.length === 0 && <div style={{ color: 'var(--muted)', fontSize: '13px' }}>No time-away blocks yet.</div>}
              </div>
            </div>

            {/* Data Export & Backup */}
            <div style={{ padding: '18px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: '8px', marginBottom: '20px' }}>
              <h3>Data Export</h3>
              <p style={{ fontSize: '13px', color: 'var(--muted)' }}>
                Export all Leaves-held local data (notes index, emails, calendar events, tasks, notifications) as JSON.
              </p>
              <button className="text-button" onClick={() => void handleExport()} style={{ marginTop: '10px' }}>
                <Download size={14} /> Export All Leaves Data (JSON)
              </button>
            </div>

            {/* Schedule Notifications Log */}
            <div style={{ padding: '18px', background: 'var(--panel)', border: '1px solid var(--line)', borderRadius: '8px' }}>
              <h3>Schedule Notifications ({notifications.length})</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '10px' }}>
                {notifications.map((n) => (
                  <div key={n.id} style={{ padding: '10px', background: 'var(--sidebar)', borderRadius: '6px', fontSize: '13px' }}>
                    <strong>{n.title}:</strong> {n.message}
                    <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>{relativeDate(n.created_at)}</div>
                  </div>
                ))}
                {notifications.length === 0 && <div style={{ color: 'var(--muted)', fontSize: '13px' }}>No notifications yet.</div>}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
export default App
