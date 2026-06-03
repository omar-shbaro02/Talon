import { CalendarCheck, ExternalLink } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api/api.js'

export default function Settings() {
  const [calendar, setCalendar] = useState(null)

  useEffect(() => {
    api.calendarStatus().then(setCalendar).catch(() => setCalendar({ connected: false }))
  }, [])

  function connectGoogle() {
    window.location.href = `${api.apiBase}/auth/google/start`
  }

  return (
    <div className="space-y-6">
      <section className="panel accent-strip rounded-lg p-5 pl-6">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-black">Calendar Integration</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Connect Google Calendar to create events and Google Meet links from TALON.</p>
          </div>
          <CalendarCheck className="text-violet-300" size={25} />
        </div>
        <div className="rounded-lg border border-blue-300/25 bg-blue-400/10 p-4">
          <div className="text-sm font-bold text-blue-200">Status</div>
          <div className="mt-1 text-2xl font-black">{calendar?.connected ? 'Connected' : 'Not Connected'}</div>
          {calendar?.google_account_email ? <div className="mt-2 text-sm text-slate-300">{calendar.google_account_email}</div> : null}
          <button className="btn-primary mt-4" onClick={connectGoogle}>
            <ExternalLink size={17} />
            Connect Google Calendar
          </button>
        </div>
      </section>

      <section className="panel rounded-lg p-5">
        <h2 className="text-xl font-black">Platform Settings</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <InfoCard label="Backend" value="http://localhost:8000" />
          <InfoCard label="AI Provider" value="OpenAI, configured by backend/.env" />
          <InfoCard label="Database" value="PostgreSQL primary, SQLite fallback" />
        </div>
      </section>
    </div>
  )
}

function InfoCard({ label, value }) {
  return (
    <div className="rounded-lg border border-violet-300/20 bg-violet-400/8 p-4">
      <div className="text-sm font-bold text-violet-200">{label}</div>
      <div className="mt-1 font-black">{value}</div>
    </div>
  )
}
