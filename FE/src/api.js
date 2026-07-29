const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  const body = response.status === 204 ? null : await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(body.detail || 'Không thể kết nối backend.')
  return body
}

export const api = {
  login: (email, password) => request('/api/cgv/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  logout: () => request('/api/cgv/logout', { method: 'POST' }),
  session: () => request('/api/cgv/session'),
  profile: () => request('/api/cgv/profile'),
  chat: (message, history) => request('/api/chat', { method: 'POST', body: JSON.stringify({ message, history }) }),
  agentVersion: () => request('/api/agent/version'),
}
