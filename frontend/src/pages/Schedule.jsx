import { CalendarPlus, ExternalLink, Video } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api/api.js'

export default function Schedule() {
  const [clients, setClients] = useState([])
  const [calendar, setCalendar] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    client_id: '',
    title: 'Executive Coaching Session',
    description: '',
    date: '',
    start_time: '10:00',
    end_time: '11:00',
    timezone: 'Asia/Beirut',
    location: '',
    attendees: '',
    talon_agent_enabled: true,
  })

  useEffect(() => {
    api.clients().then(setClients).catch(() => setClients([]))
    api.calendarStatus().then(setCalendar).catch(() => setCalendar({ connected: false }))
  }, [])

  async function submit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const payload = {
        client_id: form.client_id || null,
        title: form.title,
        description: form.description || null,
        start_time: `${form.date}T${form.start_time}:00`,
        end_time: `${form.date}T${form.end_time}:00`,
        timezone: form.timezone,
        location: form.location || null,
        attendees: form.attendees.split(',').map((email) => email.trim()).filter(Boolean),
        add_google_meet: true,
        talon_agent_enabled: form.talon_agent_enabled,
      }
      const scheduled = await api.createCalendarEvent(payload)
      setResult(scheduled)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_0.8fr]">
      <section className="panel accent-strip rounded-lg p-5 pl-6">
        <div className="mb-4 flex items-center gap-3">
          <CalendarPlus className="text-violet-300" size={24} />
          <h2 className="text-xl font-black">Schedule Session</h2>
        </div>
        {!calendar?.connected ? (
          <div className="mb-4 rounded-lg border border-blue-300/25 bg-blue-400/10 p-4 text-sm text-blue-100">
            Connect Google Calendar before scheduling sessions.
          </div>
        ) : null}
        {error ? <div className="mb-4 rounded-lg border border-red-400/40 bg-red-500/12 p-4 text-sm text-red-100">{error}</div> : null}
        <form onSubmit={submit} className="grid gap-3 md:grid-cols-2">
          <select className="field" value={form.client_id} onChange={(event) => setForm({ ...form, client_id: event.target.value })}>
            <option value="">No client selected</option>
            {clients.map((client) => <option key={client.id} value={client.id}>{client.full_name}</option>)}
          </select>
          <input className="field" required placeholder="Title" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
          <textarea className="field min-h-28 md:col-span-2" placeholder="Description" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />
          <input className="field" required type="date" value={form.date} onChange={(event) => setForm({ ...form, date: event.target.value })} />
          <input className="field" value={form.timezone} onChange={(event) => setForm({ ...form, timezone: event.target.value })} />
          <input className="field" required type="time" value={form.start_time} onChange={(event) => setForm({ ...form, start_time: event.target.value })} />
          <input className="field" required type="time" value={form.end_time} onChange={(event) => setForm({ ...form, end_time: event.target.value })} />
          <input className="field" placeholder="Location" value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} />
          <input className="field" placeholder="Attendees, comma separated" value={form.attendees} onChange={(event) => setForm({ ...form, attendees: event.target.value })} />
          <label className="flex items-center gap-3 rounded-lg border border-violet-300/20 bg-violet-400/8 p-3 text-sm font-bold">
            <input type="checkbox" checked={form.talon_agent_enabled} onChange={(event) => setForm({ ...form, talon_agent_enabled: event.target.checked })} />
            Enable TALON Meeting Agent
          </label>
          <button className="btn-primary md:col-span-2" disabled={loading || !calendar?.connected}>
            <CalendarPlus size={17} />
            {loading ? 'Scheduling...' : 'Schedule Session'}
          </button>
        </form>
      </section>

      <section className="panel rounded-lg p-5">
        <div className="mb-4 flex items-center gap-3">
          <Video className="text-blue-300" size={22} />
          <h2 className="text-xl font-black">Scheduled Output</h2>
        </div>
        {result ? (
          <div className="space-y-3">
            <OutputLink label="Google Calendar" href={result.google_html_link} />
            <OutputLink label="Google Meet" href={result.google_meet_link} />
            <div className="rounded-lg border border-violet-300/20 bg-violet-400/8 p-4">
              <div className="text-sm font-bold text-violet-200">TALON Status</div>
              <div className="mt-1 font-black">{result.talon_agent_enabled && result.google_meet_link ? 'Ready for Meeting Agent' : 'Scheduled only'}</div>
            </div>
          </div>
        ) : (
          <p className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-white/15 dark:text-slate-400">
            Created events will show Google Calendar and Meet links here.
          </p>
        )}
      </section>
    </div>
  )
}

function OutputLink({ label, href }) {
  return (
    <div className="rounded-lg border border-blue-300/20 bg-blue-400/8 p-4">
      <div className="text-sm font-bold text-blue-200">{label}</div>
      {href ? (
        <a className="mt-2 inline-flex items-center gap-2 font-black text-violet-200" href={href} target="_blank" rel="noreferrer">
          Open link <ExternalLink size={16} />
        </a>
      ) : (
        <div className="mt-2 text-sm text-slate-400">Not returned yet</div>
      )}
    </div>
  )
}
