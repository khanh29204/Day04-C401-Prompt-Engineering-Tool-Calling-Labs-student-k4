import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api.js'
import ChatPanel from './components/ChatPanel.jsx'
import CgvPanel from './components/CgvPanel.jsx'
import InspectorPanel from './components/InspectorPanel.jsx'

const INITIAL_MESSAGE = {
  id: 'welcome',
  role: 'assistant',
  content: 'Chào bạn! Mình có thể tìm phim, rạp, suất chiếu và hỗ trợ thông tin CGV.',
}

export default function App() {
  const [messages, setMessages] = useState([INITIAL_MESSAGE])
  const [pending, setPending] = useState(false)
  const [authState, setAuthState] = useState({ authenticated: false, loading: false, error: '' })
  const [profile, setProfile] = useState(null)
  const [activity, setActivity] = useState([])
  const [interactions, setInteractions] = useState([])
  const [view, setView] = useState('chat')
  const [lastMovie, setLastMovie] = useState(null)
  const [lastSeatmap, setLastSeatmap] = useState(null)

  const history = useMemo(() => messages
    .filter(({ id }) => id !== 'welcome')
    .map(({ role, content }) => ({ role, content })), [messages])

  const addActivity = useCallback((item) => {
    setActivity((current) => [{ id: crypto.randomUUID(), at: new Date().toLocaleTimeString('vi-VN'), ...item }, ...current].slice(0, 12))
  }, [])

  const addInteraction = useCallback((entry) => {
    setInteractions((current) => [{ id: crypto.randomUUID(), at: new Date().toLocaleTimeString('vi-VN'), ...entry }, ...current].slice(0, 30))
  }, [])

  const applyToolPreviews = useCallback((toolEvents) => {
    toolEvents.forEach((event) => {
      const result = event?.result
      if (!result || result.error) return

      if (event.tool === 'movie_reviews' && result.movie) {
        setLastMovie({
          title: result.movie.title,
          posterUrl: result.movie.poster_url,
          rating: result.movie.vote_average,
          meta: result.movie.release_date,
        })
      } else if ((event.tool === 'cgv_movies' || event.tool === 'cgv_cinema_schedules') && Array.isArray(result.items)) {
        const withThumbnail = result.items.find((item) => item.thumbnail)
        if (withThumbnail) {
          setLastMovie({
            title: withThumbnail.name,
            posterUrl: withThumbnail.thumbnail,
            rating: null,
            meta: withThumbnail.rating_code,
          })
        }
      } else if (event.tool === 'cgv_seatmap' && Array.isArray(result.rows)) {
        setLastSeatmap(result)
      }
    })
  }, [])

  const sendMessage = useCallback(async (content) => {
    const userMessage = { id: crypto.randomUUID(), role: 'user', content }
    setMessages((current) => [...current, userMessage])
    setPending(true)
    addActivity({ type: 'agent', title: 'Agent đang xử lý yêu cầu', detail: 'Đang chọn công cụ phù hợp', state: 'running' })
    const requestPayload = { message: content, history }
    try {
      const result = await api.chat(content, history)
      addInteraction({ request: requestPayload, response: result })
      const toolCalls = result.tool_events || []
      applyToolPreviews(toolCalls)
      toolCalls.forEach((event) => addActivity({
        type: 'tool', title: `Đã gọi ${event.tool}`, detail: event.result?.error || 'Hoàn tất', state: event.result?.error ? 'error' : 'completed',
      }))
      setMessages((current) => [...current, {
        id: crypto.randomUUID(), role: 'assistant', content: result.assistant_text || 'Mình chưa có phản hồi.', toolCalls,
      }])
    } catch (error) {
      addInteraction({ request: requestPayload, error: error.message })
      addActivity({ type: 'error', title: 'Không thể xử lý yêu cầu', detail: error.message, state: 'error' })
      setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'assistant', content: `Có lỗi: ${error.message}` }])
    } finally {
      setPending(false)
    }
  }, [addActivity, addInteraction, applyToolPreviews, history])

  const login = useCallback(async (email, password) => {
    setAuthState((state) => ({ ...state, loading: true, error: '' }))
    try {
      const result = await api.login(email, password)
      setAuthState({ ...result, authenticated: true, loading: false, error: '' })
      addActivity({ type: 'auth', title: 'Đã đăng nhập CGV', detail: 'Phiên được giữ an toàn ở backend', state: 'completed' })
    } catch (error) {
      setAuthState({ authenticated: false, loading: false, error: error.message })
    }
  }, [addActivity])

  const logout = useCallback(async () => {
    await api.logout()
    setProfile(null)
    setAuthState({ authenticated: false, loading: false, error: '' })
    addActivity({ type: 'auth', title: 'Đã đăng xuất CGV', detail: 'Phiên backend đã được xóa', state: 'completed' })
  }, [addActivity])

  const loadProfile = useCallback(async () => {
    try {
      const result = await api.profile()
      setProfile(result.profile || result)
      addActivity({ type: 'tool', title: 'Đã tải thông tin thành viên', detail: 'Preview đã được cập nhật', state: 'completed' })
    } catch (error) {
      setAuthState((state) => ({ ...state, error: error.message }))
    }
  }, [addActivity])

  useEffect(() => {
    api.session().then((result) => {
      if (result.authenticated) setAuthState((state) => ({ ...state, ...result, loading: false, error: '' }))
    }).catch(() => {})
  }, [])

  return (
    <main className="flex h-screen flex-col overflow-hidden bg-md-surface p-4 sm:p-6 lg:p-8">
      <header className="mx-auto mb-6 flex w-full max-w-[1600px] shrink-0 items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-2xl bg-md-primary text-lg font-bold text-md-onPrimary shadow-elevation1">C</div>
        <div className="flex-1"><h1 className="text-xl font-semibold tracking-tight">CGV Agent Console</h1><p className="text-sm text-md-onSurfaceVariant">Trợ lý đặt lịch xem phim an toàn</p></div>
        <nav className="flex gap-1 rounded-full bg-surface-container-high p-1" aria-label="Chuyển view">
          <button
            type="button"
            onClick={() => setView('chat')}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${view === 'chat' ? 'bg-primary text-on-primary' : 'text-on-surface-variant hover:bg-surface-container'}`}
          >
            Chat
          </button>
          <button
            type="button"
            onClick={() => setView('inspector')}
            className={`rounded-full px-4 py-2 text-sm font-semibold transition ${view === 'inspector' ? 'bg-primary text-on-primary' : 'text-on-surface-variant hover:bg-surface-container'}`}
          >
            Inspector
          </button>
        </nav>
      </header>
      {view === 'chat' ? (
        <section className="mx-auto grid w-full min-h-0 max-w-[1600px] flex-1 gap-6 lg:grid-cols-[minmax(0,1.45fr)_minmax(360px,0.8fr)]">
          <ChatPanel messages={messages} pending={pending} onSend={sendMessage} />
          <CgvPanel authState={authState} activity={activity} profile={profile} movie={lastMovie} seatmap={lastSeatmap} onLogin={({ email, password }) => login(email, password)} onLogout={logout} onLoadProfile={loadProfile} />
        </section>
      ) : (
        <section className="mx-auto flex w-full min-h-0 max-w-[1600px] flex-1 flex-col">
          <InspectorPanel interactions={interactions} />
        </section>
      )}
    </main>
  )
}
