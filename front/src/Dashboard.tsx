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
    const { state, fetchWeatherData } = useApp();

    const handleGenerateReport = async () => {
        console.log('Gerando relatório para:', {
            location: state.location,
            date: state.selectedDate,
            time: state.selectedTime
        });
        
        // Busca dados atualizados quando gerar relatório
        await fetchWeatherData();
    };

    const handleExport = () => {
        const exportData = {
            location: state.location,
            selectedDate: state.selectedDate,
            selectedTime: state.selectedTime,
            weatherData: state.weatherData,
            precipitationData: state.precipitationData,
            forecast: state.forecast
        };
        
        console.log('Exportando dados:', exportData);
        
        // TODO: Implementar exportação real (CSV, JSON)
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `weather-data-${state.selectedDate}.json`;
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
                        <CalendarCard />
                        <MapCard />
                        <ActionBar 
                            onGenerateReport={handleGenerateReport}
                            onExport={handleExport}
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