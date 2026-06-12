import { Activity, CalendarDays, CheckSquare, Lightbulb, PlayCircle, Target, Users, Zap } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/api.js'
import ActionItem from '../components/ActionItem.jsx'
import InsightCard from '../components/InsightCard.jsx'
import StatCard from '../components/StatCard.jsx'

export default function Dashboard() {
  const [summary, setSummary] = useState(null)

  useEffect(() => {
    api.dashboard().then(setSummary).catch(() => {
      setSummary({
        active_clients: 0,
        sessions_this_week: 0,
        pending_actions: 0,
        generated_insights: 0,
        today_sessions: [],
        recent_meeting_summaries: [],
        latest_recorded_sessions: [],
        ai_recommendations: ['Connect the backend to unlock live dashboard intelligence.'],
        quick_actions: [],
      })
    })
  }, [])

  const stats = [
    ['Active Clients', summary?.active_clients ?? '...', 'Current coaching relationships', Users],
    ['Sessions This Week', summary?.sessions_this_week ?? '...', 'Upcoming coaching cadence', CalendarDays],
    ['Pending Actions', summary?.pending_actions ?? '...', 'Open follow-through items', CheckSquare],
    ['Generated Insights', summary?.generated_insights ?? '...', 'AI interactions captured', Lightbulb],
  ]

  return (
    <div className="space-y-6">
      <section className="color-band rounded-lg p-5 text-white">
        <div className="relative z-10 grid gap-5 xl:grid-cols-[1fr_0.9fr] xl:items-center">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-md bg-white/16 px-3 py-1 text-xs font-black uppercase tracking-wide text-sky-100">
              <Activity size={14} />
              Executive Pulse
            </div>
            <h2 className="text-2xl font-black md:text-3xl">Coaching momentum at a glance</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-white/82">
              Prioritize the clients, actions, and meetings that need attention next.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <PulseTile icon={Users} label="Clients" value={summary?.active_clients ?? 0} />
            <PulseTile icon={Target} label="Actions" value={summary?.pending_actions ?? 0} />
            <PulseTile icon={Zap} label="Insights" value={summary?.generated_insights ?? 0} />
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map(([label, value, detail, icon]) => (
          <StatCard key={label} label={label} value={value} detail={detail} icon={icon} />
        ))}
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <CalendarWidget
          title="Today's Meetings"
          value={summary?.todays_meetings?.length ?? 0}
          detail={summary?.todays_meetings?.[0]?.title || 'No Google meetings today'}
          to="/schedule"
        />
        <CalendarWidget
          title="Upcoming Sessions"
          value={summary?.upcoming_scheduled_events?.length ?? 0}
          detail={summary?.upcoming_scheduled_events?.[0]?.title || 'Schedule from TALON'}
          to="/schedule"
        />
        <CalendarWidget
          title="Google Calendar"
          value={summary?.google_calendar_connected ? 'On' : 'Off'}
          detail={summary?.google_calendar_email || 'Connect in Settings'}
          to="/settings"
        />
        <CalendarWidget
          title="Agent Ready"
          value={summary?.talon_agent_ready_meetings?.length ?? 0}
          detail={summary?.talon_agent_ready_meetings?.[0]?.title || 'Meet links prepared'}
          to="/meetings"
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="panel rounded-lg p-5">
          <div className="mb-4 flex items-center justify-between gap-4">
            <h2 className="text-xl font-black">Today Sessions</h2>
            <Link className="btn-secondary text-sm" to="/schedule">Schedule</Link>
          </div>
          <div className="space-y-3">
            {summary?.today_sessions?.length ? (
              summary.today_sessions.map((session) => (
                <ActionItem
                  key={session.id}
                  title={`${session.title} - ${session.client_name || 'Client'}`}
                  detail={`${formatDate(session.session_date)} - ${session.status}`}
                />
              ))
            ) : (
              <p className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-white/15 dark:text-slate-400">
                No sessions scheduled for today. Open a client workspace to book one.
              </p>
            )}
          </div>
        </div>

        <div className="panel rounded-lg p-5">
          <div className="mb-4 flex items-center justify-between gap-4">
            <h2 className="text-xl font-black">Latest Meeting Summaries</h2>
            <Link className="btn-secondary text-sm" to="/meetings">Open</Link>
          </div>
          <div className="space-y-3">
            {summary?.recent_meeting_summaries?.length ? (
              summary.recent_meeting_summaries.map((meeting) => (
                <ActionItem key={meeting.id} title={meeting.title} detail={meeting.summary} />
              ))
            ) : (
              <p className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-white/15 dark:text-slate-400">
                Paste meeting notes to generate summaries, actions, commitments, and follow-up drafts.
              </p>
            )}
          </div>
        </div>
      </section>

      <section className="panel rounded-lg p-5">
        <div className="mb-4 flex items-center justify-between gap-4">
          <h2 className="text-xl font-black">Latest Recorded Sessions</h2>
          <Link className="btn-secondary text-sm" to="/meetings">Open</Link>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {summary?.latest_recorded_sessions?.length ? (
            summary.latest_recorded_sessions.map((meeting) => (
              <div key={meeting.id} className="rounded-lg border border-slate-300/40 bg-white/70 p-4 dark:border-white/12 dark:bg-white/6">
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-black">{meeting.title}</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400">{meeting.client_name}</p>
                  </div>
                  <PlayCircle className="shrink-0 text-violet-300" size={19} />
                </div>
                <div className="flex flex-wrap gap-2 text-xs font-semibold">
                  <span className="rounded-md bg-blue-100 px-2 py-1 text-blue-800 dark:bg-blue-400/12 dark:text-blue-200">Transcript: {meeting.transcript_status}</span>
                  <span className="rounded-md bg-violet-100 px-2 py-1 text-violet-800 dark:bg-violet-400/12 dark:text-violet-200">Analysis: {meeting.analysis_status}</span>
                </div>
                <Link className="mt-4 inline-flex text-sm font-bold text-violet-300" to="/meetings">Open session</Link>
              </div>
            ))
          ) : (
            <p className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-white/15 dark:text-slate-400 md:col-span-2 xl:col-span-3">
              Recorded coaching sessions will appear after TALON Assistant joins a meeting.
            </p>
          )}
        </div>
      </section>

      <section className="panel rounded-lg p-5">
        <h2 className="mb-4 text-xl font-black">AI Recommendations</h2>
        <div className="grid gap-3 md:grid-cols-3">
          {(summary?.ai_recommendations || []).map((item) => (
            <InsightCard key={item} title="Recommended Move" body={item} />
          ))}
        </div>
      </section>

      <section className="panel rounded-lg p-5">
        <h2 className="mb-4 text-xl font-black">Quick Actions</h2>
        <div className="grid gap-3 md:grid-cols-4">
          <Link to="/clients" className="btn-primary">Add Client</Link>
          <Link to="/meetings" className="btn-primary">Meeting Agent</Link>
          <Link to="/content-studio" className="btn-primary">Generate Content</Link>
          <Link to="/knowledge" className="btn-primary">Add Knowledge</Link>
        </div>
      </section>
    </div>
  )
}

function PulseTile({ icon: Icon, label, value }) {
  return (
    <div className="rounded-lg border border-white/18 bg-white/16 p-4 shadow-lg shadow-slate-950/10">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div className="flex size-10 items-center justify-center rounded-lg bg-sky-300 text-slate-950 shadow-md shadow-blue-950/15">
          <Icon size={19} />
        </div>
        <div className="text-3xl font-black">{value}</div>
      </div>
      <div className="text-sm font-black">{label}</div>
      <div className="mt-3 h-2 rounded-full bg-white/16">
        <div className="h-full rounded-full bg-sky-300" style={{ width: `${Math.min(100, 35 + Number(value || 0) * 12)}%` }} />
      </div>
    </div>
  )
}

function CalendarWidget({ title, value, detail, to }) {
  return (
    <Link to={to} className="panel accent-strip rounded-lg p-4 pl-6 transition hover:-translate-y-0.5 hover:border-violet-300">
      <div className="rainbow-rule mb-4" />
      <div className="text-sm font-black text-blue-200">{title}</div>
      <div className="mt-2 text-3xl font-black">{value}</div>
      <div className="mt-2 truncate text-sm text-slate-400">{detail}</div>
    </Link>
  )
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}
