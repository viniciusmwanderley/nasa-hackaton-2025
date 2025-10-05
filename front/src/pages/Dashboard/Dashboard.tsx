import React from 'react';
import './Dashboard.css';
import { useApp } from '../../contexts/AppContext';
import { getTimezoneFromLocationSync } from '../../utils/timezone';
import { exportWeatherDataToCSV } from '../../utils/csvExport';

// Importa todos os componentes de uma vez
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
        // Primeiro carrega os dados se não existirem
        if (!state.weatherData || !state.apiData) {
            console.log('Loading data before export...');
            await handleGenerateReport();
            
            // Aguarda um pouco para os dados serem processados
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        // Usa a função de export dedicada
        exportWeatherDataToCSV(state);
    };

    const handleGenerateReport = async () => {
        console.log('Gerando relatório para:', {
            location: state.location,
            date: state.selectedDate,
            time: state.selectedTime
        });

        // Busca dados atualizados quando gerar relatório
        await fetchWeatherData();

        // Construir parâmetros para a API
        const { latitude, longitude } = state.location;
        const selectedDate = state.selectedDate;
        const selectedTime = state.selectedTime;

        // Formatar center_datetime
        const centerDatetime = selectedTime
            ? `${selectedDate}T${selectedTime.formatted}:00Z`
            : `${selectedDate}T00:00:00Z`;

        // Detectar timezone baseado na localização
        const timezone = getTimezoneFromLocationSync(state.location);
        console.log('Timezone detectado para o relatório:', timezone);

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

        console.log('=== INICIANDO CHAMADA PARA API ===');
        console.log('Enviando parâmetros para a API:', params);

        try {
            console.log('Fazendo fetch para a API de análise do tempo');
            
            const response = await fetch('https://nasa-hackaton-2025-ten.vercel.app/weather/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });

            console.log('Response status:', response.status);
            console.log('Response ok:', response.ok);
            console.log('Response headers:', response.headers);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Erro na resposta:', errorText);
                throw new Error(`Erro na API: ${response.status} - ${response.statusText}`);
            }

            const data = await response.json();
            console.log('=== RESPOSTA DA API RECEBIDA ===');
            console.log('Dados completos da API:', JSON.stringify(data, null, 2));
            
            if (data.meta) {
                console.log('Meta informações:', data.meta);
                console.log('Latitude:', data.meta.latitude);
                console.log('Longitude:', data.meta.longitude);
                console.log('Timezone:', data.meta.target_timezone);
            }

            if (data.classifications) {
                console.log('=== CLASSIFICAÇÕES METEOROLÓGICAS ===');
                console.log('Probabilidade de chuva:', data.classifications.rain_probability);
                console.log('Percentil de calor excessivo:', data.classifications.very_hot_temp_percentile);
                console.log('Probabilidade de neve:', data.classifications.very_snowy_probability);
                console.log('Percentil de ventos fortes:', data.classifications.very_windy_percentile);
                console.log('Probabilidade de tempestade:', data.classifications.very_wet_probability);
            }

            // Os dados serão processados automaticamente pelo context
        } catch (error) {
            console.error('=== ERRO NA CHAMADA DA API ===');
            console.error('Erro completo:', error);
            if (error instanceof Error) {
                console.error('Mensagem:', error.message);
                console.error('Stack:', error.stack);
            }
        }
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