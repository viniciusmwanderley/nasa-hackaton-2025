import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom'
import './index.css'
import Dashboard from './pages/Dashboard/Dashboard.tsx'
import EnergyPanel from './pages/EnergyPanel.tsx'
import { AppProvider } from './contexts/AppContext'
import { FilterProvider } from './contexts/FilterContext'

const EnergyPanelWithNavigation = () => {
  const navigate = useNavigate()
  
  const handleBackToDashboard = () => {
    navigate('/')
  }

  return <EnergyPanel onBackToDashboard={handleBackToDashboard} />
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AppProvider>
        <FilterProvider>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/energy-panel" element={<EnergyPanelWithNavigation />} />
          </Routes>
        </FilterProvider>
      </AppProvider>
    </BrowserRouter>
  </StrictMode>,
)
