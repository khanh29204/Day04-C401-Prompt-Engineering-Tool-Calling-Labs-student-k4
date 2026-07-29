import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api.js'
import ChatPanel from './components/ChatPanel.jsx'
import CgvPanel from './components/CgvPanel.jsx'

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

  const history = useMemo(() => messages
    .filter(({ id }) => id !== 'welcome')
    .map(({ role, content }) => ({ role, content })), [messages])

  const addActivity = useCallback((item) => {
    setActivity((current) => [{ id: crypto.randomUUID(), at: new Date().toLocaleTimeString('vi-VN'), ...item }, ...current].slice(0, 12))
  }, [])

  const sendMessage = useCallback(async (content) => {
    const userMessage = { id: crypto.randomUUID(), role: 'user', content }
    setMessages((current) => [...current, userMessage])
    setPending(true)
    addActivity({ type: 'agent', title: 'Agent đang xử lý yêu cầu', detail: 'Đang chọn công cụ phù hợp', state: 'running' })
    try {
      const result = await api.chat(content, history)
      const toolCalls = result.tool_events || []
      toolCalls.forEach((event) => addActivity({
        type: 'tool', title: `Đã gọi ${event.tool}`, detail: event.result?.error || 'Hoàn tất', state: event.result?.error ? 'error' : 'completed',
      }))
      setMessages((current) => [...current, {
        id: crypto.randomUUID(), role: 'assistant', content: result.assistant_text || 'Mình chưa có phản hồi.', toolCalls,
      }])
    } catch (error) {
      addActivity({ type: 'error', title: 'Không thể xử lý yêu cầu', detail: error.message, state: 'error' })
      setMessages((current) => [...current, { id: crypto.randomUUID(), role: 'assistant', content: `Có lỗi: ${error.message}` }])
    } finally {
      setPending(false)
    }
  }, [addActivity, history])

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
    <main className="min-h-screen bg-md-surface p-4 sm:p-6 lg:p-8">
      <header className="mx-auto mb-6 flex max-w-[1600px] items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-2xl bg-md-primary text-lg font-bold text-md-onPrimary shadow-elevation1">C</div>
        <div><h1 className="text-xl font-semibold tracking-tight">CGV Agent Console</h1><p className="text-sm text-md-onSurfaceVariant">Trợ lý đặt lịch xem phim an toàn</p></div>
      </header>
      <section className="mx-auto grid max-w-[1600px] gap-6 lg:grid-cols-[minmax(0,1.45fr)_minmax(360px,0.8fr)]">
        <ChatPanel messages={messages} pending={pending} onSend={sendMessage} />
        <CgvPanel authState={authState} activity={activity} profile={profile} onLogin={({ email, password }) => login(email, password)} onLogout={logout} onLoadProfile={loadProfile} />
      </section>
    </main>
  )
}
