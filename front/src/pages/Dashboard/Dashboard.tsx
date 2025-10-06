import React from 'react';
import './Dashboard.css';
import { useApp } from '../../contexts/AppContext';
import { exportWeatherDataToCSV } from '../../utils/csvExport';

import TodayWeatherSection from '../../components/cards/TodayWeatherSection/TodayWeatherSection';
import DailyForecast from '../../components/cards/DailyForecast/DailyForecast';
import PrecipitationChartCard from '../../components/cards/PrecipitationChartCard/PrecipitationChartCard';
import CalendarCard from '../../components/cards/CalendarCard/CalendarCard';
import MapCard from '../../components/cards/MapCard/MapCard';
import RenewableEnergyCard from '../../components/cards/RenewableEnergyCard/RenewableEnergyCard';
import Header from '../../components/layout/Header/Header';
import ActionBar from '../../components/layout/ActionBar/ActionBar';

const Dashboard: React.FC = () => {
    const { state, analyzeWeather } = useApp();

    const handleExportRawData = async () => {
        if (!state.weatherData || !state.apiData) {
            await analyzeWeather();
            
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        exportWeatherDataToCSV(state);
    };

    return (
        <div className="dashboard-container">
            <Header />

            <div className="main-content">
                <div className="left-panel">
                    <TodayWeatherSection />
                    
                    <div className="forecast-row">
                        <DailyForecast />
                    </div>
                    
                    <div className="bottom-row">
                        <PrecipitationChartCard />
                        <RenewableEnergyCard />
                    </div>
                </div>

                <div className="right-panel">
                    <div className="sidebar-container">
                        <div className="report-controls">
                            <span className="header-title">Export Raw Data</span>
                        </div>
                        <CalendarCard />
                        <MapCard />
                        <ActionBar 
                            onGenerateReport={handleExportRawData}
                        />
                    </div>
                </div>
            </div>

            {state.error && (
                <div className="error-overlay">
                    <div className="error-message">
                        {state.error}
                        <button onClick={() => window.location.reload()}>
                            Tentar novamente
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Dashboard;