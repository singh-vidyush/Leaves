import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { isTauri } from '@tauri-apps/api/core'
import { open } from '@tauri-apps/plugin-dialog'
import {
  ArrowUpRight,
  CalendarDays,
  Check,
  ChevronRight,
  CircleHelp,
  Clock3,
  FileText,
  FolderPlus,
  Leaf,
  LoaderCircle,
  Moon,
  Search,
  Settings2,
  Sun,
  RefreshCw,
  X,
} from 'lucide-react'
import { api, type Dashboard, type SearchResult, type Source } from './api'

type Page = 'overview' | 'search' | 'sources'
type Theme = 'light' | 'dark'

const emptyDashboard: Dashboard = { source_count: 0, document_count: 0, sources: [], recent_documents: [] }

function timeGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

function displayDate(date: Date) {
  return new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric' }).format(date)
}

function App() {
  const [page, setPage] = useState<Page>('overview')
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('leaves-theme')
    if (saved === 'dark' || saved === 'light') return saved
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })
  const [dashboard, setDashboard] = useState<Dashboard>(emptyDashboard)
  const [serviceReady, setServiceReady] = useState(false)
  const [serviceError, setServiceError] = useState('')
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [recursive, setRecursive] = useState(true)
  const [folderPath, setFolderPath] = useState('')
  const [busy, setBusy] = useState(false)
  const [actionMessage, setActionMessage] = useState('')

  const refreshDashboard = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.dashboard()
      setDashboard(data)
      setServiceReady(true)
      setServiceError('')
    } catch {
      setDashboard(emptyDashboard)
      setServiceReady(false)
      setServiceError('Local service is not running yet.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshDashboard()
    const interval = window.setInterval(() => void refreshDashboard(), 30_000)
    return () => window.clearInterval(interval)
  }, [refreshDashboard])

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
      setSearchError(error instanceof Error ? error.message : 'Search could not be completed.')
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }

  async function selectFolder() {
    setActionMessage('')
    if (isTauri()) {
      const selected = await open({ directory: true, multiple: false, title: 'Choose a Markdown folder' })
      if (typeof selected === 'string') await addFolder(selected)
      return
    }
    setFolderPath((current) => current || '')
    document.getElementById('folder-path-input')?.focus()
  }

  async function addFolder(path = folderPath) {
    if (!path.trim()) return
    setBusy(true)
    setActionMessage('Indexing Markdown files…')
    try {
      const result = await api.addSource(path.trim(), recursive)
      setActionMessage(`Folder added. ${result.indexed} Markdown files indexed.`)
      setFolderPath('')
      await refreshDashboard()
    } catch (error) {
      setActionMessage(error instanceof Error ? error.message : 'Could not add that folder.')
    } finally {
      setBusy(false)
    }
  }

  async function refreshSource(source: Source) {
    setBusy(true)
    setActionMessage('Refreshing selected folder…')
    try {
      const result = await api.refreshSource(source.id) as { indexed: number }
      setActionMessage(`${result.indexed} Markdown files indexed.`)
      await refreshDashboard()
    } catch (error) {
      setActionMessage(error instanceof Error ? error.message : 'Refresh failed.')
    } finally {
      setBusy(false)
    }
  }

  async function removeSource(source: Source) {
    if (!window.confirm(`Remove this folder from Leaves? Its original files will stay untouched.`)) return
    setBusy(true)
    try {
      await api.removeSource(source.id)
      setActionMessage('Folder removed from Leaves. Original files were not changed.')
      await refreshDashboard()
    } catch (error) {
      setActionMessage(error instanceof Error ? error.message : 'Could not remove that folder.')
    } finally {
      setBusy(false)
    }
  }

  const setSearchAndRun = (value: string) => {
    setQuery(value)
    setPage('search')
    if (value.trim()) {
      window.setTimeout(() => {
        const form = document.getElementById('search-form') as HTMLFormElement | null
        form?.requestSubmit()
      }, 0)
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => setPage('overview')} aria-label="Leaves home">
          <span className="brand-mark"><Leaf size={18} strokeWidth={2.1} /></span>
          <span className="brand-name">leaves<span className="brand-period">.</span></span>
        </button>

        <div className="workspace-label">YOUR SPACE</div>
        <nav className="primary-nav" aria-label="Main navigation">
          <button className={`nav-item ${page === 'overview' ? 'active' : ''}`} onClick={() => setPage('overview')}>
            <span className="nav-glyph dashboard-glyph"><span /><span /><span /><span /></span>
            <span>Overview</span>
          </button>
          <button className={`nav-item ${page === 'search' ? 'active' : ''}`} onClick={() => setPage('search')}>
            <Search size={17} /><span>Search</span><kbd>⌘ K</kbd>
          </button>
          <button className={`nav-item ${page === 'sources' ? 'active' : ''}`} onClick={() => setPage('sources')}>
            <FolderPlus size={17} /><span>Sources</span>
          </button>
        </nav>

        <div className="sidebar-section-head">
          <span>CONNECTED</span><span className="section-count">{dashboard.source_count}</span>
        </div>
        <div className="connected-list">
          {dashboard.sources.length ? dashboard.sources.map((source) => (
            <button key={source.id} className="connected-source" onClick={() => setPage('sources')} title={source.path}>
              <span className="source-dot markdown-dot"><FileText size={13} /></span>
              <span className="source-name">{source.path.split('/').filter(Boolean).at(-1) ?? source.path}</span>
              <span className="source-online" />
            </button>
          )) : <div className="sidebar-empty">Add your first folder</div>}
        </div>

        <div className="sidebar-bottom">
          <div className="local-note"><span className="local-pulse" /> Stored on this device</div>
          <button className="nav-item settings-link" onClick={() => setPage('sources')}><Settings2 size={17} /><span>Settings & sources</span></button>
          <div className="profile-row">
            <div className="profile-avatar">L</div>
            <div className="profile-copy"><strong>Leaves</strong><span>Personal workspace</span></div>
            <button className="icon-button small" aria-label="About Leaves" title="About Leaves"><CircleHelp size={16} /></button>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumbs"><span>Leaves</span><ChevronRight size={14} /><strong>{pageTitle(page)}</strong></div>
          <div className="topbar-right">
            <span className={`service-state ${serviceReady ? 'online' : 'offline'}`}><span />{serviceReady ? 'Local and ready' : 'Connecting locally'}</span>
            <button className="icon-button theme-button" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`} title="Toggle appearance">
              {theme === 'light' ? <Moon size={17} /> : <Sun size={17} />}
            </button>
            <div className="avatar-small">L</div>
          </div>
        </header>

        {serviceError && <div className="service-banner"><span>{serviceError} Start the local API to index and search your notes.</span><code>cd apps/server &amp;&amp; uv run fastapi dev</code></div>}

        {page === 'overview' && <Overview
          dashboard={dashboard}
          loading={loading}
          dateText={dateText}
          onSearch={(value) => setSearchAndRun(value)}
          onNavigate={setPage}
          onAddFolder={() => void selectFolder()}
          onOpenRecent={(item) => setSearchAndRun(item.title)}
        />}
        {page === 'search' && <SearchPage
          query={query}
          setQuery={setQuery}
          runSearch={runSearch}
          results={searchResults}
          searching={searching}
          error={searchError}
          hasSources={dashboard.source_count > 0}
          onAddFolder={() => void selectFolder()}
        />}
        {page === 'sources' && <SourcesPage
          sources={dashboard.sources}
          documentCount={dashboard.document_count}
          recursive={recursive}
          setRecursive={setRecursive}
          folderPath={folderPath}
          setFolderPath={setFolderPath}
          busy={busy}
          actionMessage={actionMessage}
          onChooseFolder={() => void selectFolder()}
          onAddFolder={() => void addFolder()}
          onRefresh={refreshSource}
          onRemove={removeSource}
        />}
      </main>
    </div>
  )
}

function pageTitle(page: Page) {
  return page === 'overview' ? 'Overview' : page === 'search' ? 'Search' : 'Sources'
}

function Overview({
  dashboard, loading, dateText, onSearch, onNavigate, onAddFolder, onOpenRecent,
}: {
  dashboard: Dashboard
  loading: boolean
  dateText: string
  onSearch: (value: string) => void
  onNavigate: (page: Page) => void
  onAddFolder: () => void
  onOpenRecent: (item: Dashboard['recent_documents'][number]) => void
}) {
  return (
    <div className="page-content overview-page">
      <div className="welcome-row">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" />{dateText}</div>
          <h1>{timeGreeting()}<span className="title-comma">,</span> take a breath.</h1>
          <p className="welcome-subtitle">A little more context for the things that matter.</p>
        </div>
        <div className="sun-stamp" aria-hidden="true"><span>葉</span><i /></div>
      </div>

      <form className="hero-search" id="dashboard-search" onSubmit={(event) => { event.preventDefault(); onSearch(new FormData(event.currentTarget).get('q')?.toString() ?? '') }}>
        <Search size={20} />
        <input id="main-search-input" name="q" placeholder="Search your notes, moments, and plans…" aria-label="Search your Leaves context" />
        <kbd>⌘ K</kbd>
        <button className="search-arrow" aria-label="Search"><ArrowUpRight size={19} /></button>
      </form>

      <div className="overview-grid">
        <section className="panel day-panel">
          <div className="panel-heading">
            <div><div className="eyebrow muted-eyebrow">YOUR DAY</div><h2>Today, in context</h2></div>
            <span className="date-chip"><CalendarDays size={14} />{new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date())}</span>
          </div>
          <div className="schedule-empty">
            <div className="schedule-art"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><span className="schedule-leaf"><Leaf size={25} /></span><span className="spark spark-a">✳</span><span className="spark spark-b">·</span></div>
            <h3>Your day will take shape here</h3>
            <p>Connect your calendar and Leaves will bring your schedule and useful context together.</p>
            <button className="text-button" onClick={() => onNavigate('sources')}>Explore integrations <ArrowUpRight size={15} /></button>
          </div>
          <div className="day-footer"><span><Clock3 size={14} /> Background schedule planning</span><span className="planned-badge">IN DEVELOPMENT</span></div>
        </section>

        <section className="panel sources-panel">
          <div className="panel-heading">
            <div><div className="eyebrow muted-eyebrow">YOUR CONTEXT</div><h2>Sources</h2></div>
            <button className="icon-button" onClick={() => onNavigate('sources')} aria-label="Manage sources"><ArrowUpRight size={17} /></button>
          </div>
          <div className="stat-pair">
            <div className="stat-card"><span>Folders</span><strong>{loading ? '—' : dashboard.source_count.toString().padStart(2, '0')}</strong><small>on this device</small></div>
            <div className="stat-card"><span>Notes indexed</span><strong>{loading ? '—' : dashboard.document_count.toString().padStart(2, '0')}</strong><small>Markdown files</small></div>
          </div>
          <div className="integration-list">
            <IntegrationRow kind="markdown" title="Markdown" subtitle={dashboard.source_count ? `${dashboard.source_count} folder${dashboard.source_count === 1 ? '' : 's'} connected` : 'On-device notes'} state={dashboard.source_count ? 'connected' : 'ready'} />
            <IntegrationRow kind="gmail" title="Gmail" subtitle="Email and follow-ups" state="planned" />
            <IntegrationRow kind="calendar" title="Google Calendar" subtitle="Events and time blocks" state="planned" />
          </div>
          <button className="panel-link" onClick={() => onNavigate('sources')}>Manage sources <ChevronRight size={15} /></button>
        </section>
      </div>

      <section className="recent-section">
        <div className="section-title-row"><div><div className="eyebrow muted-eyebrow">A QUIET PULSE</div><h2>Recently in your world</h2></div><button className="text-button" onClick={() => onNavigate('search')}>Search everything <ArrowUpRight size={15} /></button></div>
        {dashboard.recent_documents.length ? <div className="recent-list">
          {dashboard.recent_documents.map((item) => <button className="recent-item" key={item.path} onClick={() => onOpenRecent(item)}>
            <span className="recent-file-icon"><FileText size={17} /></span>
            <span className="recent-copy"><strong>{item.title}</strong><small>{item.path}</small></span>
            <span className="recent-time">{relativeDate(item.modified_at)}</span><ChevronRight size={16} className="recent-chevron" />
          </button>)}
        </div> : <div className="recent-empty">
          <span className="empty-leaf"><Leaf size={17} /></span>
          <span><strong>{dashboard.source_count ? 'Nothing new since your last check-in.' : 'Your notes stay yours.'}</strong><small>{dashboard.source_count ? 'Indexed Markdown will show up here.' : 'Add a folder to let Leaves start building context, on this device.'}</small></span>
          {!dashboard.source_count && <button className="small-outline-button" onClick={onAddFolder}><FolderPlus size={15} /> Add a folder</button>}
        </div>}
      </section>

      <footer className="page-footer"><span><span className="local-pulse" /> Private by nature. Local by default.</span><span>Leaves <span className="footer-separator">·</span> Go touch some grass</span></footer>
    </div>
  )
}

function IntegrationRow({ kind, title, subtitle, state }: { kind: 'markdown' | 'gmail' | 'calendar'; title: string; subtitle: string; state: 'connected' | 'ready' | 'planned' }) {
  return <div className="integration-row">
    <span className={`integration-icon ${kind}`}>
      {kind === 'markdown' ? <FileText size={15} /> : kind === 'gmail' ? <span className="gmail-m">M</span> : <CalendarDays size={15} />}
    </span>
    <span className="integration-copy"><strong>{title}</strong><small>{subtitle}</small></span>
    {state === 'planned' ? <span className="planned-dot" title="Planned integration" /> : <span className={`connection-check ${state}`} title={state === 'connected' ? 'Connected' : 'Ready'}>{state === 'connected' && <Check size={11} />}</span>}
  </div>
}

function SearchPage({ query, setQuery, runSearch, results, searching, error, hasSources, onAddFolder }: {
  query: string
  setQuery: (query: string) => void
  runSearch: (event?: FormEvent) => void
  results: SearchResult[]
  searching: boolean
  error: string
  hasSources: boolean
  onAddFolder: () => void
}) {
  return <div className="page-content search-page">
    <div className="page-heading-block"><div className="eyebrow"><span className="eyebrow-line" />FIND YOUR THREAD</div><h1>Search your context<span className="title-comma">.</span></h1><p>Look across the things you have chosen to keep close.</p></div>
    <form className="search-page-form" id="search-form" onSubmit={runSearch}>
      <Search size={20} /><input id="main-search-input" autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Try a name, a project, or a phrase…" aria-label="Search indexed Markdown" />
      {query && <button type="button" className="icon-button clear-search" onClick={() => { setQuery(''); }} aria-label="Clear search"><X size={16} /></button>}
      <button className="solid-button" disabled={searching}>{searching ? <LoaderCircle size={16} className="spin" /> : 'Search'}</button>
    </form>
    <div className="search-meta"><span>{searching ? 'Searching your local index…' : query ? `${results.length} ${results.length === 1 ? 'result' : 'results'}` : 'Search runs on this device'}</span><span className="local-indicator"><span className="local-pulse" /> LOCAL INDEX</span></div>
    {error && <div className="inline-error">{error}</div>}
    {searching && <div className="loading-state"><LoaderCircle className="spin" size={22} /> Looking through your notes…</div>}
    {!searching && query && !error && results.length > 0 && <div className="result-list">
      {results.map((result) => <article className="result-card" key={result.id}>
        <div className="result-topline"><span className="result-type"><FileText size={14} /> Markdown</span><span>{relativeDate(result.modified_at)}</span></div>
        <h2>{result.title}</h2>
        <p>{highlightSnippet(result.excerpt)}</p>
        <div className="result-path"><span>{result.path}</span><ArrowUpRight size={14} /></div>
      </article>)}
    </div>}
    {!searching && query && !error && results.length === 0 && <div className="search-empty"><div className="empty-orbit"><Search size={22} /></div><h2>No matches yet</h2><p>Try a shorter phrase, or check that your Markdown folder is connected.</p>{!hasSources && <button className="outline-button" onClick={onAddFolder}><FolderPlus size={16} /> Add a folder</button>}</div>}
    {!query && <div className="search-start"><div className="search-start-icon"><Search size={17} /></div><div><strong>Your search stays private.</strong><p>Leaves searches only the Markdown you have indexed on this device.</p></div><span className="privacy-seal"><Leaf size={15} /> LOCAL ONLY</span></div>}
  </div>
}

function SourcesPage({ sources, documentCount, recursive, setRecursive, folderPath, setFolderPath, busy, actionMessage, onChooseFolder, onAddFolder, onRefresh, onRemove }: {
  sources: Source[]
  documentCount: number
  recursive: boolean
  setRecursive: (recursive: boolean) => void
  folderPath: string
  setFolderPath: (path: string) => void
  busy: boolean
  actionMessage: string
  onChooseFolder: () => void
  onAddFolder: () => void
  onRefresh: (source: Source) => void
  onRemove: (source: Source) => void
}) {
  return <div className="page-content sources-page">
    <div className="page-heading-block"><div className="eyebrow"><span className="eyebrow-line" />YOUR CHOSEN CONTEXT</div><h1>Sources<span className="title-comma">.</span></h1><p>Choose what Leaves can learn from. Your collected data stays on this device.</p></div>
    <section className="source-manager panel">
      <div className="manager-heading"><div className="integration-icon markdown"><FileText size={17} /></div><div><h2>Local Markdown</h2><p>Connect a folder of notes. Leaves indexes Markdown files and leaves originals untouched.</p></div><span className="live-label"><span className="local-pulse" /> ON DEVICE</span></div>
      <div className="folder-action-row"><button className="solid-button" onClick={onChooseFolder} disabled={busy}><FolderPlus size={16} /> Choose a folder</button><span>Only the folder you select is added to Leaves.</span></div>
      {!isTauri() && <form className="dev-folder-form" onSubmit={(event) => { event.preventDefault(); onAddFolder() }}>
        <label htmlFor="folder-path-input">For browser preview, enter an absolute folder path</label>
        <div><input id="folder-path-input" value={folderPath} onChange={(event) => setFolderPath(event.target.value)} placeholder="/Users/you/Documents/Notes" /><button className="small-outline-button" disabled={busy || !folderPath.trim()}>Add path</button></div>
      </form>}
      <label className="toggle-row"><span className="toggle-copy"><strong>Include subfolders</strong><small>Scan Markdown files inside nested folders too.</small></span><input type="checkbox" checked={recursive} onChange={(event) => setRecursive(event.target.checked)} /><span className="toggle-ui" /></label>
      {actionMessage && <div className={`action-message ${actionMessage.toLowerCase().includes('could not') || actionMessage.toLowerCase().includes('failed') ? 'error' : ''}`}>{busy && <LoaderCircle size={15} className="spin" />}{actionMessage}</div>}
    </section>

    <div className="source-list-heading"><div><div className="eyebrow muted-eyebrow">CONNECTED TO LEAVES</div><h2>Your folders <span>{sources.length}</span></h2></div><div className="indexed-total">{documentCount} notes indexed</div></div>
    {sources.length ? <div className="source-cards">{sources.map((source) => <article className="source-card panel" key={source.id}>
      <div className="source-card-main"><div className="source-folder-icon"><FileText size={19} /></div><div className="source-card-copy"><h3>{source.path.split('/').filter(Boolean).at(-1) ?? source.path}</h3><p title={source.path}>{source.path}</p><div className="source-card-meta"><span><span className="local-pulse" /> {source.recursive ? 'Including subfolders' : 'Selected folder only'}</span><span>Last scanned {source.last_indexed_at ? relativeDate(source.last_indexed_at) : 'not yet'}</span></div></div></div>
      <div className="source-card-actions"><button className="icon-button" onClick={() => onRefresh(source)} disabled={busy} aria-label="Refresh folder" title="Refresh folder"><RefreshCw size={15} /></button><button className="icon-button remove-source" onClick={() => onRemove(source)} disabled={busy} aria-label="Remove folder" title="Remove from Leaves"><X size={16} /></button></div>
    </article>)}</div> : <div className="source-empty panel"><div className="empty-folder-art"><FolderPlus size={24} /></div><h3>No folders connected yet</h3><p>Choose a Markdown folder to begin. Leaves stores an indexed copy on this device; it never changes or deletes the original files.</p><button className="solid-button" onClick={onChooseFolder} disabled={busy}><FolderPlus size={16} /> Choose your first folder</button></div>}

    <section className="planned-integrations"><div className="section-title-row"><div><div className="eyebrow muted-eyebrow">PRIORITIZED NEXT</div><h2>Planned integrations</h2></div><span className="planned-label">NOT CONNECTED</span></div>
      <div className="planned-grid"><PlannedCard title="Gmail" desc="Find commitments and follow-ups in your inbox." icon="gmail" /><PlannedCard title="Google Calendar" desc="Arrange your day around events and available time." icon="calendar" /><PlannedCard title="More schedule apps" desc="Connect supported sources you choose." icon="apps" /></div>
    </section>
    <div className="data-control-note"><span className="privacy-seal"><Leaf size={15} /> YOUR DATA</span><span>Removing a folder deletes its indexed copy from Leaves. Your original files stay where they are.</span></div>
  </div>
}

function PlannedCard({ title, desc, icon }: { title: string; desc: string; icon: 'gmail' | 'calendar' | 'apps' }) {
  return <article className="planned-card"><div className={`integration-icon ${icon}`}>{icon === 'gmail' ? <span className="gmail-m">M</span> : icon === 'calendar' ? <CalendarDays size={16} /> : <Settings2 size={16} />}</div><div><strong>{title}</strong><p>{desc}</p></div><span className="planned-tag">NEXT</span></article>
}

function relativeDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.valueOf())) return 'recently'
  const days = Math.floor((Date.now() - date.getTime()) / 86_400_000)
  if (days <= 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days} days ago`
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(date)
}

function highlightSnippet(value: string) {
  const pieces = value.split(/(\u0001.*?\u0002)/g)
  return pieces.map((piece, index) => {
    if (piece.startsWith('\u0001') && piece.endsWith('\u0002')) {
      return <mark key={index}>{piece.slice(1, -1)}</mark>
    }
    return piece
  })
}

export default App
