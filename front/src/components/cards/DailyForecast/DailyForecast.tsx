import React from 'react';
import './DailyForecast.css';
import { useApp } from '../../../contexts/AppContext';

const DailyForecast: React.FC = () => {
    const { state } = useApp();
    const { forecast, selectedTime } = state;

    // Converte dia da semana de acordo com os dados (baseado na posição)
    const getDayName = (dayInitial: string, index: number) => {
        const dayNames = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
        return dayNames[index] || dayInitial;
    };

    return (
        <div className="daily-forecast-card">
            <div className="forecast-container">
                {forecast.map((day, index) => (
                    <div key={index} className="forecast-day">
                        <div className="day-name">{getDayName(day.dayInitial, index)}</div>
                        <div className="temp-range">
                            {selectedTime ? (
                                // Quando horário definido, mostra temperatura única
                                day.temperature ? `${day.temperature}°C` : 'N/A'
                            ) : (
                                // Quando horário não definido, mostra min/max
                                day.minTemperature && day.maxTemperature 
                                    ? `${day.minTemperature}°C → ${day.maxTemperature}°C`
                                    : 'N/A'
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default DailyForecast;