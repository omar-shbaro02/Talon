const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Request failed with ${response.status}`)
  }
  if (response.status === 204) return null
  return response.json()
}

export const api = {
  apiBase: API_BASE,
  health: () => request('/health'),
  dashboard: () => request('/dashboard/summary'),
  calendarStatus: () => request('/calendar/status'),
  calendarEvents: () => request('/calendar/events'),
  createCalendarEvent: (payload) => request('/calendar/events', { method: 'POST', body: JSON.stringify(payload) }),
  updateCalendarEvent: (id, payload) => request(`/calendar/events/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteCalendarEvent: (id) => request(`/calendar/events/${id}`, { method: 'DELETE' }),
  sendCalendarAgent: (id) => request(`/calendar/events/${id}/send-agent`, { method: 'POST' }),
  clients: () => request('/clients'),
  client: (id) => request(`/clients/${id}`),
  createClient: (payload) => request('/clients', { method: 'POST', body: JSON.stringify(payload) }),
  updateClient: (id, payload) => request(`/clients/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteClient: (id) => request(`/clients/${id}`, { method: 'DELETE' }),
  sessions: (params = {}) => {
    const query = new URLSearchParams(params)
    return request(`/sessions${query.toString() ? `?${query}` : ''}`)
  },
  createSession: (payload) => request('/sessions', { method: 'POST', body: JSON.stringify(payload) }),
  updateSession: (id, payload) => request(`/sessions/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  sendSessionInvite: (id) => request(`/sessions/${id}/send-invite`, { method: 'POST' }),
  analyzeCoach: (payload) => request('/coach/analyze', { method: 'POST', body: JSON.stringify(payload) }),
  analyzeMeeting: (payload) => request('/meetings/analyze', { method: 'POST', body: JSON.stringify(payload) }),
  analyzeStoredMeeting: (id) => request(`/meetings/${id}/analyze`, { method: 'POST' }),
  meetings: () => request('/meetings'),
  joinMeetingAgent: (payload) => request('/meeting-agent/join', { method: 'POST', body: JSON.stringify(payload) }),
  meetingAgentStatus: (id) => request(`/meeting-agent/${id}/status`),
  meetingTranscript: (id) => request(`/meetings/${id}/transcript`),
  deleteMeetingRecordingData: (id) => request(`/meetings/${id}/recording-data`, { method: 'DELETE' }),
  knowledge: () => request('/knowledge'),
  createKnowledge: (payload) => request('/knowledge', { method: 'POST', body: JSON.stringify(payload) }),
  deleteKnowledge: (id) => request(`/knowledge/${id}`, { method: 'DELETE' }),
  generateContent: (payload) => request('/content/generate', { method: 'POST', body: JSON.stringify(payload) }),
}
