import { Bot, BrainCircuit, CalendarDays, FileText, Home, Library, Network, Settings, Users } from 'lucide-react'
import { NavLink } from 'react-router-dom'

const navItems = [
  { to: '/', label: 'Dashboard', icon: Home },
  { to: '/clients', label: 'Clients', icon: Users },
  { to: '/meetings', label: 'Meeting Agent', icon: BrainCircuit },
  { to: '/schedule', label: 'Schedule', icon: CalendarDays },
  { to: '/knowledge', label: 'Knowledge', icon: Library },
  { to: '/content-studio', label: 'Content', icon: FileText },
  { to: '/automations', label: 'Automations', icon: Network },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export default function Sidebar() {
  return (
    <aside className="hidden w-72 shrink-0 border-r border-white/12 bg-slate-950 px-4 py-5 text-white lg:block">
      <div className="mb-8 flex items-center gap-3 px-2">
        <div className="flex size-12 items-center justify-center rounded-lg bg-gradient-to-br from-sky-400 via-blue-500 to-violet-600 text-white shadow-lg shadow-blue-500/25">
          <Bot size={24} />
        </div>
        <div>
          <div className="text-xl font-black tracking-wide">TALON</div>
          <div className="text-xs font-semibold uppercase text-sky-200/85">Coaching Intelligence</div>
        </div>
      </div>
      <div className="mb-5 grid grid-cols-5 gap-1 px-2">
        <span className="h-1.5 rounded-full bg-sky-300" />
        <span className="h-1.5 rounded-full bg-blue-300" />
        <span className="h-1.5 rounded-full bg-indigo-300" />
        <span className="h-1.5 rounded-full bg-violet-300" />
      </div>
      <nav className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-3 text-sm font-semibold transition ${
                  isActive ? 'bg-gradient-to-r from-sky-400/28 via-blue-500/24 to-violet-500/28 text-white shadow-lg shadow-blue-950/25' : 'text-slate-300 hover:bg-white/10 hover:text-white'
                }`
              }
            >
              <Icon size={18} />
              {item.label}
            </NavLink>
          )
        })}
      </nav>
    </aside>
  )
}
