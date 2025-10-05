import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import Dashboard from './pages/Dashboard/Dashboard.tsx'
import EnergyPanel from './pages/EnergyPanel.tsx'
import { AppProvider } from './contexts/AppContext'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AppProvider>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/energy-panel" element={<EnergyPanel />} />
        </Routes>
      </AppProvider>
    </BrowserRouter>
  </StrictMode>,
)
