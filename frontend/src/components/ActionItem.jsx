import { CircleCheck } from 'lucide-react'

export default function ActionItem({ title, detail }) {
  return (
    <div className="flex gap-3 rounded-lg border border-blue-200/70 bg-white/75 p-3 dark:border-blue-300/14 dark:bg-blue-400/6">
      <CircleCheck size={18} className="mt-0.5 shrink-0 text-violet-400" />
      <div>
        <div className="text-sm font-bold text-slate-950 dark:text-white">{title}</div>
        {detail && <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{detail}</div>}
      </div>
    </div>
  )
}
