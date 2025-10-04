import React from 'react';
import './DailyForecast.css';

// Dados da previsão semanal baseados na captura de tela
const weeklyForecast = [
    { day: 'SEG', minTemp: 18, maxTemp: 28 },
    { day: 'TER', minTemp: 18, maxTemp: 28 },
    { day: 'QUA', minTemp: 18, maxTemp: 28 },
    { day: 'QUI', minTemp: 18, maxTemp: 28 },
    { day: 'SEX', minTemp: 18, maxTemp: 28 },
    { day: 'SAB', minTemp: 18, maxTemp: 28 },
    { day: 'DOM', minTemp: 18, maxTemp: 28 },
];

const DailyForecast: React.FC = () => {

    return (
        <div className="daily-forecast-card">
            <div className="forecast-container">
                {weeklyForecast.map((day, index) => (
                    <div key={index} className="forecast-day">
                        <div className="day-name">{day.day}</div>
                        <div className="temp-range">
                            {day.minTemp}°C → {day.maxTemp}°C
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default DailyForecast;