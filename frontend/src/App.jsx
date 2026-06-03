import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import Sidebar from './components/Sidebar.jsx'
import Topbar from './components/Topbar.jsx'
import Automations from './pages/Automations.jsx'
import ClientDetail from './pages/ClientDetail.jsx'
import Clients from './pages/Clients.jsx'
import ContentStudio from './pages/ContentStudio.jsx'
import Dashboard from './pages/Dashboard.jsx'
import KnowledgeHub from './pages/KnowledgeHub.jsx'
import MeetingIntelligence from './pages/MeetingIntelligence.jsx'
import Schedule from './pages/Schedule.jsx'
import Settings from './pages/Settings.jsx'

const titles = {
  '/': 'Command Center',
  '/clients': 'Client Workspaces',
  '/meetings': 'Meeting Agent',
  '/schedule': 'Schedule Session',
  '/knowledge': 'Knowledge Hub',
  '/content-studio': 'Content Studio',
  '/automations': 'Automation Preview',
  '/settings': 'Settings',
}

export default function App() {
  const location = useLocation()
  const pageTitle = location.pathname.startsWith('/clients/') ? 'Client Workspace' : titles[location.pathname] || 'TALON'

  return (
    <div className="executive-bg dark min-h-screen text-slate-100">
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="min-w-0 flex-1 px-4 py-4 md:px-6 lg:px-8">
          <Topbar title={pageTitle} />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/clients" element={<Clients />} />
            <Route path="/clients/:id" element={<ClientDetail />} />
            <Route path="/meetings" element={<MeetingIntelligence />} />
            <Route path="/schedule" element={<Schedule />} />
            <Route path="/knowledge" element={<KnowledgeHub />} />
            <Route path="/content-studio" element={<ContentStudio />} />
            <Route path="/automations" element={<Automations />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
