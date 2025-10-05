import React from 'react';
import './Dashboard.css';
import { useApp } from '../../contexts/AppContext';
import { getTimezoneFromLocationSync } from '../../utils/timezone';
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
    const { state, fetchWeatherData } = useApp();

    const handleExportRawData = async () => {
        if (!state.weatherData || !state.apiData) {
            await handleGenerateReport();
            
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        exportWeatherDataToCSV(state);
    };

    const handleGenerateReport = async () => {
        await fetchWeatherData();

        const { latitude, longitude } = state.location;
        const selectedDate = state.selectedDate;
        const selectedTime = state.selectedTime;

        const centerDatetime = selectedTime
            ? `${selectedDate}T${selectedTime.formatted}:00Z`
            : `${selectedDate}T00:00:00Z`;

        const timezone = getTimezoneFromLocationSync(state.location);

        const params = {
            latitude,
            longitude,
            center_datetime: centerDatetime,
            target_timezone: timezone,
            days_before: 3,
            days_after: 3,
            granularity: selectedTime ? 'hourly' : 'daily',
            window_days: 7,
            ...(selectedTime && {
                start_year: 2015,
                hourly_chunk_years: 5
            })
        };

        try {            
            const response = await fetch('https://nasa-hackaton-2025-ten.vercel.app/weather/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Error in response:', errorText);
                throw new Error(`API Error: ${response.status} - ${response.statusText}`);
            }
        } catch (error) {
            console.error('=== API CALL ERROR ===');
            console.error('Complete error:', error);
            if (error instanceof Error) {
                console.error('Message:', error.message);
                console.error('Stack:', error.stack);
            }
        }
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