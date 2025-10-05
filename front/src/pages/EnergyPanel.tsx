import React, { useState } from 'react';
import './EnergyPanel.css';
import FilterBar from '../components/energy/FilterBar/FilterBar';
import EnergyChart from '../components/energy/EnergyChart/EnergyChart';
import CityRanking from '../components/energy/CityRanking/CityRanking';
import PlaceholderCards from '../components/energy/PlaceholderCards/PlaceholderCards';

const EnergyPanel: React.FC = () => {
    const [selectedMonth, setSelectedMonth] = useState('Selecione um mês');
    const [selectedUnit, setSelectedUnit] = useState('Unidades de Geração');
    const [selectedLocation, setSelectedLocation] = useState('Selecione um Local');

    return (
        <div className="energy-panel">
            <header className="energy-panel-header">
                <div className="logo">
                    <img src="/weatherdata.png" alt="CLIMADATA" className="logo-image" />
                </div>
                <h1 className="panel-title">PAINEL DE INSIGHTS RELACIONADOS</h1>
            </header>

            <div className="energy-panel-content">
                <FilterBar
                    selectedMonth={selectedMonth}
                    onMonthChange={setSelectedMonth}
                    selectedUnit={selectedUnit}
                    onUnitChange={setSelectedUnit}
                    selectedLocation={selectedLocation}
                    onLocationChange={setSelectedLocation}
                />

                <div className="charts-section">
                    <div className="energy-section">
                        <div className="chart-container">
                            <EnergyChart 
                                type="solar"
                                title="Estimativa mensal Geração de energia solar"
                            />
                        </div>
                        <div className="ranking-container">
                            <CityRanking energyType="solar" />
                        </div>
                    </div>
                    
                    <div className="energy-section">
                        <div className="chart-container">
                            <EnergyChart 
                                type="eolica"
                                title="Estimativa mensal Geração de energia eólica"
                            />
                        </div>
                        <div className="ranking-container">
                            <CityRanking energyType="eolica" />
                        </div>
                    </div>
                </div>

                <PlaceholderCards />
            </div>
        </div>
    );
};

export default EnergyPanel;
