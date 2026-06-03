import { Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api/api.js'

export default function KnowledgeHub() {
  const [docs, setDocs] = useState([])
  const [form, setForm] = useState({ title: '', category: '', tags: '', content: '' })

  const load = () => api.knowledge().then(setDocs).catch(() => setDocs([]))

  useEffect(() => {
    load()
  }, [])

  async function submit(event) {
    event.preventDefault()
    await api.createKnowledge({
      title: form.title,
      category: form.category || null,
      content: form.content,
      tags: form.tags.split(',').map((tag) => tag.trim()).filter(Boolean),
    })
    setForm({ title: '', category: '', tags: '', content: '' })
    await load()
  }

  async function remove(id) {
    await api.deleteKnowledge(id)
    await load()
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
      <form onSubmit={submit} className="panel rounded-lg p-5">
        <h2 className="mb-4 text-xl font-black">Add Knowledge Document</h2>
        <div className="space-y-3">
          <input className="field" required placeholder="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <input className="field" placeholder="Category" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} />
          <input className="field" placeholder="Tags, separated by commas" value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} />
          <textarea className="field min-h-72" required placeholder="Frameworks, notes, principles, exercises, methodology..." value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} />
          <button className="btn-primary">Save Knowledge</button>
        </div>
      </form>
      <section className="space-y-4">
        {docs.map((doc) => (
          <article key={doc.id} className="panel rounded-lg p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-black">{doc.title}</h3>
                <p className="mt-1 text-sm font-semibold text-violet-600 dark:text-violet-200">{doc.category || 'General'}</p>
              </div>
              <button className="btn-secondary p-2" title="Delete knowledge document" onClick={() => remove(doc.id)}>
                <Trash2 size={16} />
              </button>
            </div>
            <p className="mt-3 line-clamp-4 text-sm leading-6 text-slate-600 dark:text-slate-300">{doc.content}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {(doc.tags || []).map((tag) => <span key={tag} className="rounded-md bg-blue-100 px-2 py-1 text-xs font-bold text-blue-800 dark:bg-blue-400/12 dark:text-blue-200">{tag}</span>)}
            </div>
          </article>
        ))}
      </section>
    </div>
  )
}
