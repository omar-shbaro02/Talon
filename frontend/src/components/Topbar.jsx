import { Bell, Search, Sparkles } from 'lucide-react'

export default function Topbar({ title }) {
  return (
    <header className="color-band mb-6 flex flex-col gap-4 rounded-lg px-4 py-4 text-white md:flex-row md:items-center md:justify-between">
      <div className="relative z-10">
        <div className="mb-2 inline-flex rounded-md bg-white/16 px-2 py-1 text-xs font-black uppercase tracking-wide text-blue-100">TALON</div>
        <h1 className="text-2xl font-black md:text-3xl">{title}</h1>
        <div className="mt-3 grid max-w-md grid-cols-4 gap-1">
          <span className="h-1.5 rounded-full bg-sky-200" />
          <span className="h-1.5 rounded-full bg-blue-200" />
          <span className="h-1.5 rounded-full bg-indigo-200" />
          <span className="h-1.5 rounded-full bg-violet-200" />
        </div>
      </div>
      <div className="relative z-10 flex items-center gap-2">
        <div className="hidden items-center gap-2 rounded-lg border border-white/18 bg-white/16 px-3 py-2 shadow-lg shadow-slate-950/10 md:flex">
          <Search size={16} className="text-sky-100" />
          <span className="text-sm text-white/86">Search clients, notes, actions</span>
        </div>
        <button className="btn-secondary border-white/18 bg-white/16 text-white" title="AI status">
          <Sparkles size={17} className="text-violet-100" />
        </button>
        <button className="btn-secondary border-white/18 bg-white/16 text-white" title="Notifications">
          <Bell size={17} className="text-sky-100" />
        </button>
      </div>
    </header>
  )
}
