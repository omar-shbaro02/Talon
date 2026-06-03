import { Brain, CalendarPlus, Clock, Download, Mail, Save } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/api.js'
import InsightCard from '../components/InsightCard.jsx'

export default function ClientDetail() {
  const { id } = useParams()
  const [client, setClient] = useState(null)
  const [prompt, setPrompt] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [sessions, setSessions] = useState([])
  const [latestInvite, setLatestInvite] = useState(null)
  const [sessionForm, setSessionForm] = useState({
    title: 'Executive coaching session',
    session_date: '',
    duration_minutes: 60,
    location: '',
    notes: '',
    status: 'scheduled',
  })
  const [loading, setLoading] = useState(false)
  const [scheduling, setScheduling] = useState(false)

  useEffect(() => {
    api.client(id).then(setClient)
    api.sessions({ client_id: id, upcoming_only: true }).then(setSessions).catch(() => setSessions([]))
  }, [id])

  async function scheduleSession(event) {
    event.preventDefault()
    setScheduling(true)
    setLatestInvite(null)
    try {
      const created = await api.createSession({
        client_id: id,
        title: sessionForm.title,
        session_date: new Date(sessionForm.session_date).toISOString(),
        duration_minutes: Number(sessionForm.duration_minutes),
        location: sessionForm.location || null,
        notes: sessionForm.notes || null,
        status: sessionForm.status,
      })
      const invite = await api.sendSessionInvite(created.id)
      const scheduled = { ...created, invite_status: invite.delivery_status }
      setLatestInvite(invite)
      setSessions([scheduled, ...sessions].sort((a, b) => new Date(a.session_date) - new Date(b.session_date)))
      setSessionForm({
        title: 'Executive coaching session',
        session_date: '',
        duration_minutes: 60,
        location: '',
        notes: '',
        status: 'scheduled',
      })
    } finally {
      setScheduling(false)
    }
  }

  async function askCoach(event) {
    event.preventDefault()
    setLoading(true)
    try {
      setAnalysis(await api.analyzeCoach({ client_id: id, prompt, context: `${client?.goals || ''}\n${client?.challenges || ''}` }))
    } finally {
      setLoading(false)
    }
  }

  function downloadInvite() {
    if (!latestInvite?.ics_content) return
    const file = new Blob([latestInvite.ics_content], { type: 'text/calendar;charset=utf-8' })
    const url = URL.createObjectURL(file)
    const link = document.createElement('a')
    link.href = url
    link.download = 'talon-session.ics'
    link.click()
    URL.revokeObjectURL(url)
  }

  if (!client) return <div className="panel rounded-lg p-6">Loading client workspace...</div>

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.2fr]">
        <section className="panel rounded-lg p-5">
          <h2 className="text-2xl font-black">{client.full_name}</h2>
          <p className="mt-1 text-slate-500 dark:text-slate-400">{client.job_title || 'Leader'} at {client.company || 'Independent'}</p>
          <dl className="mt-6 grid gap-4">
            {[
              ['Email', client.email],
              ['Phone', client.phone],
              ['Industry', client.industry],
              ['Status', client.status],
            ].map(([label, value]) => (
              <div key={label} className="rounded-lg border border-slate-200/70 p-3 dark:border-white/10">
                <dt className="text-xs font-bold uppercase text-slate-500">{label}</dt>
                <dd className="mt-1 font-semibold">{value || 'Not set'}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-5 space-y-4">
            <InsightCard title="Goals" body={client.goals || 'Add goals to sharpen coaching intelligence.'} />
            <InsightCard title="Challenges" body={client.challenges || 'Add challenges to surface better risks and next steps.'} />
          </div>
        </section>

        <section className="panel rounded-lg p-5">
          <div className="mb-4 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-black">Schedule Session</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Create a calendar invite and email it to the client.</p>
            </div>
            <CalendarPlus className="text-violet-300" size={24} />
          </div>
          <form onSubmit={scheduleSession} className="grid gap-3 md:grid-cols-2">
            <input className="field" required placeholder="Session title" value={sessionForm.title} onChange={(e) => setSessionForm({ ...sessionForm, title: e.target.value })} />
            <input className="field" required type="datetime-local" value={sessionForm.session_date} onChange={(e) => setSessionForm({ ...sessionForm, session_date: e.target.value })} />
            <select className="field" value={sessionForm.duration_minutes} onChange={(e) => setSessionForm({ ...sessionForm, duration_minutes: e.target.value })}>
              <option value="30">30 minutes</option>
              <option value="45">45 minutes</option>
              <option value="60">60 minutes</option>
              <option value="90">90 minutes</option>
            </select>
            <input className="field" placeholder="Location or meeting link" value={sessionForm.location} onChange={(e) => setSessionForm({ ...sessionForm, location: e.target.value })} />
            <select className="field" value={sessionForm.status} onChange={(e) => setSessionForm({ ...sessionForm, status: e.target.value })}>
              <option value="scheduled">Scheduled</option>
              <option value="confirmed">Confirmed</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
            <textarea className="field min-h-24 md:col-span-2" placeholder="Agenda, prep notes, meeting link, intake questions..." value={sessionForm.notes} onChange={(e) => setSessionForm({ ...sessionForm, notes: e.target.value })} />
            <button className="btn-primary md:col-span-2" disabled={scheduling}>
              <Mail size={17} />
              {scheduling ? 'Scheduling and preparing invite...' : 'Schedule and Send Invite'}
            </button>
          </form>

          {latestInvite && (
            <div className="mt-5 rounded-lg border border-violet-300/25 bg-violet-50/80 p-4 dark:bg-violet-400/8">
              <div className="font-black">
                {latestInvite.delivery_status === 'sent' ? 'Invitation sent' : 'Email draft ready'}
              </div>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                Recipient: {latestInvite.recipient_email || 'Add a client email to send directly'}
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                {latestInvite.mailto_url && (
                  <a className="btn-secondary" href={latestInvite.mailto_url}>
                    <Mail size={16} />
                    Open Email Draft
                  </a>
                )}
                <button className="btn-secondary" type="button" onClick={downloadInvite}>
                  <Download size={16} />
                  Download .ics
                </button>
              </div>
            </div>
          )}

          <div className="mt-5">
            <h3 className="mb-3 font-black">Upcoming Sessions</h3>
            <div className="space-y-2">
              {sessions.length ? sessions.map((session) => (
                <div key={session.id} className="flex gap-3 rounded-lg border border-slate-200/70 bg-white/65 p-3 dark:border-white/10 dark:bg-white/5">
                  <Clock size={18} className="mt-0.5 shrink-0 text-blue-300" />
                  <div>
                    <div className="font-bold">{session.title}</div>
                    <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                      {formatDate(session.session_date)} - {session.duration_minutes} min - {session.status}
                    </div>
                    <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                      Invite: {session.invite_status || 'not_sent'}
                    </div>
                    {session.location && <div className="mt-2 text-sm text-slate-600 dark:text-slate-300">{session.location}</div>}
                    {session.notes && <div className="mt-2 text-sm text-slate-600 dark:text-slate-300">{session.notes}</div>}
                  </div>
                </div>
              )) : (
                <p className="rounded-lg border border-dashed border-slate-300 p-4 text-sm text-slate-500 dark:border-white/15 dark:text-slate-400">
                  No sessions scheduled yet.
                </p>
              )}
            </div>
          </div>
        </section>
      </div>

      <section className="panel rounded-lg p-5">
        <h2 className="mb-4 text-xl font-black">AI Coach Agent</h2>
        <form onSubmit={askCoach} className="space-y-3">
          <textarea className="field min-h-36" required placeholder="Ask TALON for coaching advice, frameworks, risks, or suggested questions." value={prompt} onChange={(e) => setPrompt(e.target.value)} />
          <button className="btn-primary" disabled={loading}>
            <Brain size={17} />
            {loading ? 'Analyzing...' : 'Analyze Coaching Prompt'}
          </button>
        </form>
        {analysis && (
          <div className="mt-5 space-y-4">
            <InsightCard title="Analysis" body={analysis.analysis} />
            <InsightCard title="Framework" body={analysis.recommended_framework} />
            <div className="grid gap-3 md:grid-cols-2">
              <List title="Suggested Questions" items={analysis.suggested_questions} />
              <List title="Next Steps" items={analysis.next_steps} />
            </div>
          </div>
        )}
      </section>
    </div>
  )
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function List({ title, items = [] }) {
  return (
    <div className="rounded-lg border border-slate-200/70 p-4 dark:border-white/10">
      <div className="mb-2 flex items-center gap-2 font-black"><Save size={16} />{title}</div>
      <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
        {items.map((item) => <li key={item}>- {item}</li>)}
      </ul>
    </div>
  )
}
