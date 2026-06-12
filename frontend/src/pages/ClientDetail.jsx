import { Brain, Save } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/api.js'
import InsightCard from '../components/InsightCard.jsx'
import ScheduleMeetingForm from '../components/ScheduleMeetingForm.jsx'

export default function ClientDetail() {
  const { id } = useParams()
  const [client, setClient] = useState(null)
  const [prompt, setPrompt] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.client(id).then(setClient)
  }, [id])

  async function askCoach(event) {
    event.preventDefault()
    setLoading(true)
    try {
      setAnalysis(await api.analyzeCoach({ client_id: id, prompt, context: `${client?.goals || ''}\n${client?.challenges || ''}` }))
    } finally {
      setLoading(false)
    }
  }

  if (!client) return <div className="panel rounded-lg p-6">Loading client workspace...</div>

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[minmax(20rem,0.75fr)_minmax(44rem,1.55fr)]">
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

        <ScheduleMeetingForm
          initialClientId={id}
          initialClientName={client.full_name}
          lockClient
          title="Schedule Meeting"
          subtitle="Create the same Google Calendar session used from the dashboard."
        />
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
