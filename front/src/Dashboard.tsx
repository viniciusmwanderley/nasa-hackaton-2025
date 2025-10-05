import React from 'react';
import './Dashboard.css';
import { useApp } from './contexts/AppContext';

// Importa todos os componentes de uma vez
import { 
    TodayWeatherSection,
    DailyForecast, 
    PrecipitationChartCard, 
    CalendarCard, 
    MapCard, 
    RenewableEnergyCard, 
    Header, 
    ActionBar 
} from './components';

const Dashboard: React.FC = () => {
    const { state, fetchWeatherData, setSelectedTime } = useApp(); // Added setSelectedTime

    const handleGenerateReport = async () => {
        console.log('Gerando relatório para:', {
            location: state.location,
            date: state.selectedDate,
            time: state.selectedTime
        });
        
        // Busca dados atualizados quando gerar relatório
        await fetchWeatherData();

        // Generate CSV data
        const exportData = [
            {
                Location: state.location.city,
                Date: state.selectedDate,
                Time: state.selectedTime?.formatted || 'All Day',
                Temperature: state.weatherData?.temperature || 'N/A', // Added null check
                Description: state.weatherData?.description || 'N/A' // Added null check
            },
            ...state.forecast.map(forecast => ({
                Date: forecast.date,
                MinTemperature: forecast.minTemperature,
                MaxTemperature: forecast.maxTemperature,
                Condition: forecast.condition
            }))
        ];

        const csvContent = exportData.map(row => Object.values(row).join(',')).join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `weather-report-${state.selectedDate}.csv`;
        link.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="dashboard-container">
            <Header />

            <div className="main-content">
                {/* Coluna Principal - Esquerda (3 linhas) */}
                <div className="left-panel">
                    {/* Linha 1: Seção Clima Hoje com cards de métricas */}
                    <TodayWeatherSection />
                    
                    {/* Linha 2: Daily Forecast - agora usa dados do contexto */}
                    <div className="forecast-row">
                        <DailyForecast />
                    </div>
                    
                    {/* Linha 3: Precipitações + Energia lado a lado */}
                    <div className="bottom-row">
                        <PrecipitationChartCard />
                        <RenewableEnergyCard />
                    </div>
                </div>

                {/* Coluna Lateral - Direita (Container com fundo claro) */}
                <div className="right-panel">
                    <div className="sidebar-container">
                        <div className="report-controls">
                            <span className="header-title">Create Report</span>
                            <div className="time-select-container"> {/* Added container for spacing */}
                                <select 
                                    className="time-select" 
                                    value={state.selectedTime?.hour ?? ''} 
                                    onChange={(event) => {
                                        const value = event.target.value;
                                        if (value === '') {
                                            setSelectedTime(null); // Corrected usage
                                        } else {
                                            const hour = parseInt(value);
                                            if (!isNaN(hour)) {
                                                setSelectedTime({ // Corrected usage
                                                    hour,
                                                    formatted: `${hour.toString().padStart(2, '0')}:00`
                                                });
                                            }
                                        }
                                    }}
                                >
                                    {[{ hour: undefined, formatted: 'All Day' },
                                    ...Array.from({ length: 24 }, (_, i) => ({
                                        hour: i,
                                        formatted: `${i.toString().padStart(2, '0')}:00`
                                    }))].map(({ hour, formatted }, index) => (
                                        <option key={index} value={hour ?? ''}>
                                            {formatted}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <CalendarCard />
                        <MapCard />
                        <ActionBar 
                            onGenerateReport={handleGenerateReport} // Removed onExport
                        />
                    </div>
                </div>
            </div>

            {/* Loading indicator quando buscando dados */}
            {state.isLoading && (
                <div className="loading-overlay">
                    <div className="loading-message">
                        Carregando dados meteorológicos...
                    </div>
                </div>
            )}

            {/* Error message se houver erro */}
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