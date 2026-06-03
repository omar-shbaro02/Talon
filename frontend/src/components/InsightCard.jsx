import { Sparkles } from 'lucide-react'

export default function InsightCard({ title, body }) {
  return (
    <div className="rounded-lg border border-violet-300/25 bg-violet-50/75 p-4 dark:border-violet-300/18 dark:bg-violet-400/9">
      <div className="flex items-center gap-2 text-sm font-black text-violet-800 dark:text-violet-200">
        <Sparkles size={16} />
        {title}
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-300">{body}</p>
    </div>
  )
}
