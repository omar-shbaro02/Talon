import { Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api/api.js'
import ClientCard from '../components/ClientCard.jsx'

const emptyForm = {
  full_name: '',
  email: '',
  phone: '',
  company: '',
  job_title: '',
  industry: '',
  goals: '',
  challenges: '',
  status: 'active',
}

export default function Clients() {
  const [clients, setClients] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [loading, setLoading] = useState(false)

  const loadClients = () => api.clients().then(setClients).catch(() => setClients([]))

  useEffect(() => {
    loadClients()
  }, [])

  async function submit(event) {
    event.preventDefault()
    setLoading(true)
    try {
      await api.createClient(Object.fromEntries(Object.entries(form).map(([key, value]) => [key, value || null])))
      setForm(emptyForm)
      await loadClients()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr_1.4fr]">
      <form onSubmit={submit} className="panel rounded-lg p-5">
        <h2 className="mb-4 text-xl font-black">Create Client Workspace</h2>
        <div className="grid gap-3">
          <input className="field" placeholder="Full name" required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          <input className="field" placeholder="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <input className="field" placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <div className="grid gap-3 md:grid-cols-2">
            <input className="field" placeholder="Company" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
            <input className="field" placeholder="Job title" value={form.job_title} onChange={(e) => setForm({ ...form, job_title: e.target.value })} />
          </div>
          <input className="field" placeholder="Industry" value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} />
          <textarea className="field min-h-24" placeholder="Goals" value={form.goals} onChange={(e) => setForm({ ...form, goals: e.target.value })} />
          <textarea className="field min-h-24" placeholder="Challenges" value={form.challenges} onChange={(e) => setForm({ ...form, challenges: e.target.value })} />
          <button className="btn-primary" disabled={loading}>
            <Plus size={17} />
            {loading ? 'Creating...' : 'Create Client'}
          </button>
        </div>
      </form>

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-black">Active Workspaces</h2>
          <span className="text-sm font-bold text-slate-500 dark:text-slate-400">{clients.length} clients</span>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {clients.map((client) => <ClientCard key={client.id} client={client} />)}
        </div>
      </section>
    </div>
  )
}

