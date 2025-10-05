import React from 'react';
import './DailyForecast.css';
import { useApp } from '../../../contexts/AppContext';
import { DailyForecastSkeleton } from '../../common/SkeletonLoader';

const DailyForecast: React.FC = () => {
    const { state } = useApp();
    const { forecast, selectedDate } = state;

    // Gera os nomes dos dias baseado na data selecionada (centro) com 3 antes e 3 depois
    const getDayNames = () => {
        const selectedDateObj = new Date(selectedDate + 'T00:00:00');
        const dayNames = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
        const days = [];
        
        // 3 dias antes, dia selecionado, 3 dias depois
        for (let i = -3; i <= 3; i++) {
            const currentDate = new Date(selectedDateObj);
            currentDate.setDate(selectedDateObj.getDate() + i);
            const dayName = dayNames[currentDate.getDay()];
            const isSelected = i === 0; // Dia selecionado é quando i = 0
            days.push({ dayName, isSelected, date: currentDate.toISOString().split('T')[0] });
        }
        
        return days;
    };

    const daysList = getDayNames();

    // Se está carregando, mostra skeleton
    if (state.isLoading) {
        return <DailyForecastSkeleton />;
    }

    return (
        <div className="daily-forecast-card">
            <div className="forecast-container">
                {daysList.map(({ dayName, isSelected, date }, index) => {
                    // Busca os dados do forecast correspondente ao dia
                    const dayData = forecast[index] || {};
                    
                    return (
                        <div 
                            key={date} 
                            className={`forecast-day ${isSelected ? 'selected-day' : ''}`}
                        >
                            <div className="day-name">{dayName}</div>
                            <div className="temp-range">
                                {dayData.temperature !== undefined ? (
                                    // Horário específico definido - mostra temperatura única
                                    `${dayData.temperature}°C`
                                ) : (
                                    // Horário não definido - mostra min/max
                                    dayData.minTemperature !== undefined && dayData.maxTemperature !== undefined 
                                        ? `${dayData.minTemperature}°C → ${dayData.maxTemperature}°C`
                                        : '--°C'
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default DailyForecast;