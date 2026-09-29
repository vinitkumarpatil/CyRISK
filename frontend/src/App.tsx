// App router: public /login, everything else behind auth inside the Layout shell.

import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { ReactNode } from 'react'
import { useAuth } from './auth/AuthContext'
import { Loading } from './components/ui'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import RiskAnalysis from './pages/RiskAnalysis'
import Assets from './pages/Assets'
import Vulnerabilities from './pages/Vulnerabilities'
import Controls from './pages/Controls'
import Recommendations from './pages/Recommendations'
import Scenarios from './pages/Scenarios'
import Optimizer from './pages/Optimizer'
import Frameworks from './pages/Frameworks'
import Assumptions from './pages/Assumptions'
import Assistant from './pages/Assistant'
import ModelCard from './pages/ModelCard'
import DataSources from './pages/DataSources'
import Reports from './pages/Reports'

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const loc = useLocation()
  if (loading) return <div className="grid h-full place-items-center"><Loading label="Restoring session…" /></div>
  if (!user) return <Navigate to="/login" replace state={{ from: loc }} />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
        <Route index element={<Dashboard />} />
        <Route path="risk" element={<RiskAnalysis />} />
        <Route path="assets" element={<Assets />} />
        <Route path="vulnerabilities" element={<Vulnerabilities />} />
        <Route path="controls" element={<Controls />} />
        <Route path="recommendations" element={<Recommendations />} />
        <Route path="scenarios" element={<Scenarios />} />
        <Route path="optimizer" element={<Optimizer />} />
        <Route path="frameworks" element={<Frameworks />} />
        <Route path="assumptions" element={<Assumptions />} />
        <Route path="assistant" element={<Assistant />} />
        <Route path="model" element={<ModelCard />} />
        <Route path="telemetry" element={<DataSources />} />
        <Route path="reports" element={<Reports />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
