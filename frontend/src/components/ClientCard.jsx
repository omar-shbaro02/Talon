import { ArrowRight, Building2 } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function ClientCard({ client }) {
  return (
    <Link to={`/clients/${client.id}`} className="panel accent-strip block rounded-lg p-5 pl-6 transition hover:-translate-y-0.5 hover:border-violet-300">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-black text-slate-950 dark:text-white">{client.full_name}</h3>
          <p className="mt-1 flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
            <Building2 size={15} />
            {client.company || 'Independent'} {client.job_title ? `- ${client.job_title}` : ''}
          </p>
        </div>
        <ArrowRight size={18} className="text-violet-400" />
      </div>
      <div className="mt-4 flex flex-wrap gap-2 text-xs font-bold">
        <span className="rounded-md bg-blue-100 px-2 py-1 text-blue-800 dark:bg-blue-400/12 dark:text-blue-200">{client.status}</span>
        {client.industry && <span className="rounded-md bg-violet-100 px-2 py-1 text-violet-800 dark:bg-violet-400/12 dark:text-violet-200">{client.industry}</span>}
      </div>
    </Link>
  )
}
