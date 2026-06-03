import { WandSparkles } from 'lucide-react'
import { useState } from 'react'
import { api } from '../api/api.js'

const types = ['linkedin_post', 'workshop_outline', 'coaching_exercise', 'article', 'session_plan', 'email']
const tones = ['professional', 'warm', 'executive', 'motivational']

export default function ContentStudio() {
  const [form, setForm] = useState({ type: 'linkedin_post', topic: '', tone: 'executive', context: '' })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setLoading(true)
    try {
      setResult(await api.generateContent(form))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
      <form onSubmit={submit} className="panel rounded-lg p-5">
        <h2 className="mb-4 text-xl font-black">Generate Coaching Content</h2>
        <div className="space-y-3">
          <select className="field" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
            {types.map((type) => <option key={type} value={type}>{type.replaceAll('_', ' ')}</option>)}
          </select>
          <select className="field" value={form.tone} onChange={(e) => setForm({ ...form, tone: e.target.value })}>
            {tones.map((tone) => <option key={tone} value={tone}>{tone}</option>)}
          </select>
          <input className="field" required placeholder="Topic" value={form.topic} onChange={(e) => setForm({ ...form, topic: e.target.value })} />
          <textarea className="field min-h-56" placeholder="Optional context" value={form.context} onChange={(e) => setForm({ ...form, context: e.target.value })} />
          <button className="btn-primary" disabled={loading}>
            <WandSparkles size={17} />
            {loading ? 'Generating...' : 'Generate'}
          </button>
        </div>
      </form>
      <section className="panel rounded-lg p-5">
        <h2 className="mb-4 text-xl font-black">Studio Output</h2>
        {result ? (
          <article>
            <h3 className="text-2xl font-black">{result.title}</h3>
            <pre className="mt-4 whitespace-pre-wrap rounded-lg bg-slate-950 p-5 text-sm leading-7 text-slate-100">{result.content}</pre>
          </article>
        ) : (
          <p className="rounded-lg border border-dashed border-slate-300 p-6 text-sm text-slate-500 dark:border-white/15 dark:text-slate-400">
            Generate LinkedIn posts, workshop outlines, coaching exercises, articles, session plans, and email drafts.
          </p>
        )}
      </section>
    </div>
  )
}

