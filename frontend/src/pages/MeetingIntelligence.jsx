import { Bot, ClipboardList, FileText, Mail, ShieldCheck, Sparkles, Trash2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/api.js'
import InsightCard from '../components/InsightCard.jsx'

const consentNotice = 'This meeting may be recorded and transcribed by TALON Assistant.'

export default function MeetingIntelligence() {
  const [clients, setClients] = useState([])
  const [meetings, setMeetings] = useState([])
  const [form, setForm] = useState({ client_id: '', title: '', meeting_url: '' })
  const [manualForm, setManualForm] = useState({ client_id: '', title: '', transcript: '' })
  const [selectedId, setSelectedId] = useState('')
  const [status, setStatus] = useState(null)
  const [transcript, setTranscript] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [manualLoading, setManualLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    refresh()
    api.clients().then(setClients).catch(() => setClients([]))
  }, [])

  useEffect(() => {
    if (!selectedId) return
    loadMeeting(selectedId)
  }, [selectedId])

  async function refresh() {
    const allMeetings = await api.meetings().catch(() => [])
    setMeetings(allMeetings)
    if (!selectedId && allMeetings.length) setSelectedId(allMeetings[0].id)
  }

  async function loadMeeting(id) {
    const meeting = meetings.find((item) => item.id === id)
    setResult(meeting || null)
    api.meetingAgentStatus(id).then(setStatus).catch(() => setStatus(null))
    api.meetingTranscript(id).then(setTranscript).catch(() => setTranscript(null))
  }

  async function sendAssistant(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await api.joinMeetingAgent({ ...form, client_id: form.client_id || null })
      await refresh()
      setSelectedId(response.meeting_id)
      setStatus({
        meeting_id: response.meeting_id,
        title: form.title,
        bot_status: response.status,
        transcript_status: 'pending',
        recording_status: 'pending',
        analysis_status: 'pending',
      })
      setForm({ client_id: '', title: '', meeting_url: '' })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function analyzeManual(event) {
    event.preventDefault()
    setManualLoading(true)
    setError('')
    try {
      const analyzed = await api.analyzeMeeting({ ...manualForm, client_id: manualForm.client_id || null })
      setResult(analyzed)
      setMeetings([analyzed, ...meetings])
      setSelectedId(analyzed.id)
      setManualForm({ client_id: '', title: '', transcript: '' })
    } catch (err) {
      setError(err.message)
    } finally {
      setManualLoading(false)
    }
  }

  async function analyzeStored() {
    if (!selectedId) return
    setLoading(true)
    setError('')
    try {
      const analyzed = await api.analyzeStoredMeeting(selectedId)
      setResult(analyzed)
      setMeetings(meetings.map((meeting) => meeting.id === analyzed.id ? analyzed : meeting))
      setStatus({ ...status, analysis_status: analyzed.analysis_status })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function deleteRecordingData() {
    if (!selectedId) return
    setLoading(true)
    setError('')
    try {
      await api.deleteMeetingRecordingData(selectedId)
      await refresh()
      setTranscript(null)
      setStatus(status ? { ...status, transcript_status: 'deleted', recording_status: 'deleted', analysis_status: 'deleted' } : null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const selectedMeeting = useMemo(() => meetings.find((meeting) => meeting.id === selectedId), [meetings, selectedId])

  return (
    <div className="space-y-6">
      {error ? <div className="rounded-lg border border-red-400/40 bg-red-500/12 p-4 text-sm text-red-100">{error}</div> : null}

      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="panel rounded-lg p-5">
          <div className="mb-4 flex items-center gap-3">
            <Bot className="text-blue-300" size={22} />
            <h2 className="text-xl font-black">Start Meeting Agent</h2>
          </div>
          <form onSubmit={sendAssistant} className="space-y-3">
            <select className="field" value={form.client_id} onChange={(event) => setForm({ ...form, client_id: event.target.value })}>
              <option value="">No client selected</option>
              {clients.map((client) => <option key={client.id} value={client.id}>{client.full_name}</option>)}
            </select>
            <input className="field" placeholder="Meeting title" required value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
            <input className="field" placeholder="Zoom, Google Meet, or Teams link" required value={form.meeting_url} onChange={(event) => setForm({ ...form, meeting_url: event.target.value })} />
            <div className="rounded-lg border border-blue-300/28 bg-blue-400/10 p-3 text-sm text-blue-50">
              <div className="flex items-start gap-2">
                <ShieldCheck className="mt-0.5 shrink-0" size={17} />
                <span>{consentNotice}</span>
              </div>
            </div>
            <button className="btn-primary w-full" disabled={loading}>
              <Bot size={17} />
              {loading ? 'Sending...' : 'Send TALON Assistant'}
            </button>
          </form>
        </div>

        <div className="panel rounded-lg p-5">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-black">Active Meeting Status</h2>
            <select className="field max-w-sm" value={selectedId} onChange={(event) => setSelectedId(event.target.value)}>
              <option value="">Select meeting</option>
              {meetings.map((meeting) => <option key={meeting.id} value={meeting.id}>{meeting.title}</option>)}
            </select>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <StatusStep label="Bot joining" active={['creating', 'created', 'configuration_required'].includes(status?.bot_status)} complete={['in_meeting', 'completed'].includes(status?.bot_status)} />
            <StatusStep label="Bot in meeting" active={status?.bot_status === 'in_meeting'} complete={status?.bot_status === 'completed'} />
            <StatusStep label="Recording" active={status?.recording_status === 'recording'} complete={status?.recording_status === 'complete'} />
            <StatusStep label="Transcript processing" active={status?.transcript_status === 'processing'} complete={status?.transcript_status === 'complete'} />
            <StatusStep label="Analysis complete" active={status?.analysis_status === 'processing'} complete={status?.analysis_status === 'complete'} />
          </div>
          {selectedMeeting ? (
            <div className="mt-4 flex flex-wrap gap-2">
              <button className="btn-secondary text-sm" onClick={analyzeStored} disabled={loading}>
                <Sparkles size={16} />
                Analyze
              </button>
              <button className="btn-secondary text-sm" onClick={deleteRecordingData} disabled={loading}>
                <Trash2 size={16} />
                Delete transcript
              </button>
            </div>
          ) : null}
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        <div className="panel rounded-lg p-5">
          <div className="mb-4 flex items-center gap-3">
            <FileText className="text-sky-300" size={21} />
            <h2 className="text-xl font-black">Transcript Viewer</h2>
          </div>
          <div className="max-h-[32rem] space-y-3 overflow-auto pr-1">
            {transcript?.segments?.length ? (
              transcript.segments.map((segment) => (
                <div key={segment.id} className="rounded-lg bg-slate-100 p-3 text-sm dark:bg-white/6">
                  <div className="mb-1 flex flex-wrap items-center gap-2 text-xs font-bold text-blue-300">
                    <span>{formatSeconds(segment.start_time_seconds)}</span>
                    <span>{segment.speaker_name || 'Speaker'}</span>
                  </div>
                  <p className="leading-6 text-slate-700 dark:text-slate-200">{segment.text}</p>
                </div>
              ))
            ) : (
              <p className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-white/15 dark:text-slate-400">
                Timestamped transcript segments will appear after Recall.ai sends transcript data.
              </p>
            )}
          </div>
        </div>

        <div className="panel rounded-lg p-5">
          <div className="mb-4 flex items-center gap-3">
            <Sparkles className="text-violet-300" size={21} />
            <h2 className="text-xl font-black">AI Analysis Panel</h2>
          </div>
          {result ? (
            <div className="space-y-4">
              <InsightCard title="Summary" body={result.summary || 'Analysis pending.'} />
              <GridList title="Action Items" items={result.recommended_next_steps} />
              <GridList title="Decisions" items={result.decisions} />
              <GridList title="Coaching Observations" items={result.coaching_observations} />
              <GridList title="Leadership Patterns" items={result.leadership_patterns} />
              <InsightCard title="Follow-Up Email" body={result.follow_up_email || 'Draft will appear after analysis.'} />
            </div>
          ) : (
            <p className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-white/15 dark:text-slate-400">
              Select a meeting or send TALON Assistant to generate coaching intelligence.
            </p>
          )}
        </div>
      </section>

      <section className="panel rounded-lg p-5">
        <div className="mb-4 flex items-center gap-3">
          <ClipboardList className="text-blue-300" size={21} />
          <h2 className="text-xl font-black">Analyze Pasted Notes</h2>
        </div>
        <form onSubmit={analyzeManual} className="grid gap-3 xl:grid-cols-[16rem_1fr]">
          <select className="field" value={manualForm.client_id} onChange={(event) => setManualForm({ ...manualForm, client_id: event.target.value })}>
            <option value="">No client selected</option>
            {clients.map((client) => <option key={client.id} value={client.id}>{client.full_name}</option>)}
          </select>
          <input className="field" placeholder="Meeting title" required value={manualForm.title} onChange={(event) => setManualForm({ ...manualForm, title: event.target.value })} />
          <textarea className="field min-h-40 xl:col-span-2" placeholder="Paste transcript or raw notes" required value={manualForm.transcript} onChange={(event) => setManualForm({ ...manualForm, transcript: event.target.value })} />
          <button className="btn-primary xl:col-span-2" disabled={manualLoading}>
            <Mail size={17} />
            {manualLoading ? 'Generating...' : 'Generate Summary'}
          </button>
        </form>
      </section>
    </div>
  )
}

function StatusStep({ label, active, complete }) {
  return (
    <div className={`rounded-lg border p-3 text-sm ${complete ? 'border-blue-300/35 bg-blue-400/10' : active ? 'border-violet-300/35 bg-violet-400/10' : 'border-slate-300/35 bg-white/40 dark:border-white/10 dark:bg-white/5'}`}>
      <div className="font-black">{label}</div>
      <div className="mt-1 text-xs font-semibold text-slate-500 dark:text-slate-400">{complete ? 'Complete' : active ? 'In progress' : 'Pending'}</div>
    </div>
  )
}

function GridList({ title, items = [] }) {
  return (
    <div>
      <h3 className="mb-2 font-black">{title}</h3>
      <div className="grid gap-2 md:grid-cols-2">
        {(items || []).length ? items.map((item) => (
          <div className="rounded-lg bg-slate-100 p-3 text-sm dark:bg-white/6" key={JSON.stringify(item)}>
            {typeof item === 'string' ? item : item.title || JSON.stringify(item)}
          </div>
        )) : <div className="rounded-lg bg-slate-100 p-3 text-sm text-slate-500 dark:bg-white/6 dark:text-slate-400">Pending analysis</div>}
      </div>
    </div>
  )
}

function formatSeconds(value) {
  const seconds = Math.max(0, Math.floor(Number(value || 0)))
  return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`
}
