import { Bot, CalendarPlus, Check, Clock, ExternalLink, Mail, MonitorUp, ShieldCheck, UserRound, Video } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/api.js'

const defaultTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Beirut'
const timeSlots = [
  '08:00',
  '08:30',
  '09:00',
  '09:30',
  '10:00',
  '10:30',
  '11:00',
  '11:30',
  '12:00',
  '13:00',
  '13:30',
  '14:00',
  '14:30',
  '15:00',
  '15:30',
  '16:00',
  '16:30',
  '17:00',
]
const durations = [30, 45, 60, 90]
const providers = [
  ['google_meet', 'Google Meet'],
  ['teams', 'Teams'],
  ['zoom', 'Zoom'],
]

function todayValue() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function addMinutes(time, minutes) {
  const [hours, mins] = time.split(':').map(Number)
  const total = hours * 60 + mins + minutes
  const endHours = Math.floor(total / 60) % 24
  const endMins = total % 60
  return `${String(endHours).padStart(2, '0')}:${String(endMins).padStart(2, '0')}`
}

function displayTime(time) {
  const [hours, minutes] = time.split(':').map(Number)
  return new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(2026, 0, 1, hours, minutes))
}

export default function ScheduleMeetingForm({
  initialClientId = '',
  initialClientName = '',
  lockClient = false,
  title = 'Schedule Session',
  subtitle = 'Create a Google Calendar event with a Google Meet link.',
}) {
  const [clients, setClients] = useState([])
  const [calendar, setCalendar] = useState(null)
  const [result, setResult] = useState(null)
  const [invite, setInvite] = useState(null)
  const [agentDispatch, setAgentDispatch] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    client_id: initialClientId,
    title: 'Executive Coaching Session',
    description: '',
    date: todayValue(),
    start_time: '10:00',
    duration_minutes: 60,
    timezone: defaultTimezone,
    location: '',
    attendees: '',
    meeting_provider: 'google_meet',
    talon_agent_enabled: true,
  })

  useEffect(() => {
    if (!lockClient) api.clients().then(setClients).catch(() => setClients([]))
    api.calendarStatus().then(setCalendar).catch(() => setCalendar({ connected: false }))
  }, [lockClient])

  useEffect(() => {
    setForm((current) => ({ ...current, client_id: initialClientId }))
  }, [initialClientId])

  const selectedClient = useMemo(() => {
    if (lockClient) return initialClientName
    return clients.find((client) => client.id === form.client_id)?.full_name || ''
  }, [clients, form.client_id, initialClientName, lockClient])
  const providerReady = Boolean(calendar?.meeting_providers?.[form.meeting_provider])

  async function submit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    setInvite(null)
    setAgentDispatch(null)
    try {
      const endTime = addMinutes(form.start_time, Number(form.duration_minutes))
      const payload = {
        client_id: form.client_id || null,
        title: form.title,
        description: form.description || null,
        start_time: `${form.date}T${form.start_time}:00`,
        end_time: `${form.date}T${endTime}:00`,
        timezone: form.timezone,
        location: form.location || null,
        attendees: form.attendees.split(',').map((email) => email.trim()).filter(Boolean),
        meeting_provider: form.meeting_provider,
        add_google_meet: form.meeting_provider === 'google_meet',
        talon_agent_enabled: form.talon_agent_enabled,
      }
      setResult(await api.createCalendarEvent(payload))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function sendInvite() {
    if (!result?.id) return
    setLoading(true)
    setError('')
    try {
      setInvite(await api.sendCalendarInvite(result.id))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function sendAgent() {
    if (!result?.id) return
    setLoading(true)
    setError('')
    try {
      setAgentDispatch(await api.sendCalendarAgent(result.id))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-w-0 grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(18rem,0.72fr)]">
      <section className="panel accent-strip min-w-0 rounded-lg p-5 pl-6">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <CalendarPlus className="text-sky-300" size={24} />
              <h2 className="text-xl font-black">{title}</h2>
            </div>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>
          </div>
          {selectedClient ? (
            <div className="hidden items-center gap-2 rounded-md border border-sky-300/25 bg-sky-400/10 px-3 py-2 text-sm font-bold text-sky-100 md:flex">
              <UserRound size={15} />
              {selectedClient}
            </div>
          ) : null}
        </div>

        {form.meeting_provider === 'google_meet' && !calendar?.connected ? (
          <div className="mb-4 rounded-lg border border-blue-300/25 bg-blue-400/10 p-4 text-sm text-blue-100">
            Connect Google Calendar before generating Google Meet links.
          </div>
        ) : null}
        {form.meeting_provider !== 'google_meet' && calendar && !providerReady ? (
          <div className="mb-4 rounded-lg border border-amber-300/25 bg-amber-400/10 p-4 text-sm text-amber-100">
            Configure {providerLabel(form.meeting_provider)} API credentials in the backend environment before generating this link.
          </div>
        ) : null}
        {error ? <div className="mb-4 rounded-lg border border-red-400/40 bg-red-500/12 p-4 text-sm text-red-100">{error}</div> : null}

        <form onSubmit={submit} className="grid gap-4">
          <div className="grid gap-3 lg:grid-cols-2">
            {lockClient ? (
              <div className="field flex items-center gap-2 font-bold">
                <UserRound size={16} />
                {initialClientName || 'Selected client'}
              </div>
            ) : (
              <select className="field" value={form.client_id} onChange={(event) => setForm({ ...form, client_id: event.target.value })}>
                <option value="">No client selected</option>
                {clients.map((client) => <option key={client.id} value={client.id}>{client.full_name}</option>)}
              </select>
            )}
            <input className="field" required placeholder="Title" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
          </div>

          <textarea className="field min-h-28" placeholder="Description" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} />

          <div className="provider-row">
            {providers.map(([value, label]) => (
              <button
                className={`provider-option ${form.meeting_provider === value ? 'provider-option-active' : ''}`}
                key={value}
                type="button"
                onClick={() => setForm({ ...form, meeting_provider: value })}
              >
                <MonitorUp size={16} />
                {label}
                {calendar && !calendar.meeting_providers?.[value] ? <span className="text-xs font-semibold opacity-70">Setup needed</span> : null}
              </button>
            ))}
          </div>

          <div className="scheduler-box">
            <div className="scheduler-meta-row">
              <label className="grid min-w-0 gap-2 text-sm font-bold text-slate-600 dark:text-slate-300">
                Date
                <input className="field" required type="date" value={form.date} onChange={(event) => setForm({ ...form, date: event.target.value })} />
              </label>
              <div>
                <div className="mb-2 text-sm font-bold text-slate-600 dark:text-slate-300">Duration</div>
                <div className="duration-row">
                  {durations.map((duration) => (
                    <button
                      className={`duration-pill ${Number(form.duration_minutes) === duration ? 'duration-pill-active' : ''}`}
                      key={duration}
                      type="button"
                      onClick={() => setForm({ ...form, duration_minutes: duration })}
                    >
                      {duration}m
                    </button>
                  ))}
                </div>
              </div>
              <label className="grid min-w-0 gap-2 text-sm font-bold text-slate-600 dark:text-slate-300">
                Timezone
                <input className="field" value={form.timezone} onChange={(event) => setForm({ ...form, timezone: event.target.value })} />
              </label>
            </div>

            <div className="mt-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-bold text-slate-600 dark:text-slate-300">
                <Clock size={16} />
                Start time
              </div>
              <div className="time-grid">
                {timeSlots.map((slot) => (
                  <button
                    className={`time-slot ${form.start_time === slot ? 'time-slot-active' : ''}`}
                    key={slot}
                    type="button"
                    onClick={() => setForm({ ...form, start_time: slot })}
                  >
                    {displayTime(slot)}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <input className="field" placeholder="Location" value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} />
            <input className="field" placeholder="Attendees, comma separated" value={form.attendees} onChange={(event) => setForm({ ...form, attendees: event.target.value })} />
          </div>

          <label className="flex items-center gap-3 rounded-lg border border-sky-300/20 bg-sky-400/8 p-3 text-sm font-bold">
            <input type="checkbox" checked={form.talon_agent_enabled} onChange={(event) => setForm({ ...form, talon_agent_enabled: event.target.checked })} />
            Enable TALON Meeting Agent
          </label>

          <button className="btn-primary" disabled={loading || (calendar && !providerReady)}>
            <CalendarPlus size={17} />
            {loading ? 'Generating...' : `Generate ${providerLabel(form.meeting_provider)} Link`}
          </button>
        </form>
      </section>

      <section className="panel min-w-0 rounded-lg p-5">
        <div className="mb-4 flex items-center gap-3">
          <Video className="text-sky-300" size={22} />
          <h2 className="text-xl font-black">Scheduled Output</h2>
        </div>
        {result ? (
          <div className="space-y-3">
            <OutputLink label={providerLabel(result.meeting_provider)} href={result.meeting_link || result.google_meet_link} />
            <OutputLink label="Google Calendar" href={result.google_html_link} />
            <div className="rounded-lg border border-emerald-300/20 bg-emerald-400/8 p-4">
              <div className="flex items-center gap-2 text-sm font-bold text-emerald-200">
                <Check size={16} />
                TALON Status
              </div>
              <div className="mt-1 font-black">{result.talon_agent_enabled && (result.meeting_link || result.google_meet_link) ? 'Ready for Meeting Agent' : 'Scheduled only'}</div>
            </div>
            {result.talon_agent_enabled && (result.meeting_link || result.google_meet_link) ? (
              <button className="btn-secondary w-full text-sm" type="button" disabled={loading} onClick={sendAgent}>
                <Bot size={17} />
                {loading ? 'Sending assistant...' : 'Send TALON Assistant'}
              </button>
            ) : null}
            {agentDispatch ? (
              <div className="rounded-lg border border-blue-300/28 bg-blue-400/10 p-4">
                <div className="flex items-start gap-2 text-sm text-blue-50">
                  <ShieldCheck className="mt-0.5 shrink-0" size={17} />
                  <span>{agentDispatch.consent_notice}</span>
                </div>
                <div className="mt-2 text-sm font-bold text-slate-300">Bot status: {agentDispatch.status}</div>
              </div>
            ) : null}
            <button className="btn-primary w-full" type="button" disabled={loading} onClick={sendInvite}>
              <Mail size={17} />
              {loading ? 'Preparing email...' : 'Send Email Invite'}
            </button>
            {invite ? (
              <div className="rounded-lg border border-sky-300/20 bg-sky-400/8 p-4">
                <div className="text-sm font-bold text-sky-200">{invite.delivery_status === 'sent' ? 'Email sent' : 'Email draft ready'}</div>
                <div className="mt-1 text-sm text-slate-400">Recipient: {invite.recipient_email || 'Add an attendee or client email'}</div>
                {invite.mailto_url ? (
                  <a className="mt-3 inline-flex items-center gap-2 font-black text-violet-200" href={invite.mailto_url}>
                    Open email draft <ExternalLink size={16} />
                  </a>
                ) : null}
              </div>
            ) : null}
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

function providerLabel(provider) {
  return {
    google_meet: 'Google Meet',
    teams: 'Teams',
    zoom: 'Zoom',
  }[provider] || 'Meeting'
}

function OutputLink({ label, href }) {
  return (
    <div className="rounded-lg border border-sky-300/20 bg-sky-400/8 p-4">
      <div className="text-sm font-bold text-sky-200">{label}</div>
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
