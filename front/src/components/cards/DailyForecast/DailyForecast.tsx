import React from 'react';
import './DailyForecast.css';
import { useApp } from '../../../contexts/AppContext';
import { DailyForecastSkeleton } from '../../common/SkeletonLoader';

const DailyForecast: React.FC = () => {
    const { state } = useApp();
    const { forecast, selectedDate } = state;

    const getDayNames = () => {
        const selectedDateObj = new Date(selectedDate + 'T00:00:00');
        const dayNames = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
        const days = [];
        
        for (let i = -3; i <= 3; i++) {
            const currentDate = new Date(selectedDateObj);
            currentDate.setDate(selectedDateObj.getDate() + i);
            const dayName = dayNames[currentDate.getDay()];
            const isSelected = i === 0; 
            days.push({ dayName, isSelected, date: currentDate.toISOString().split('T')[0] });
        }
        
        return days;
    };

    const daysList = getDayNames();

    if (state.isLoading) {
        return <DailyForecastSkeleton />;
    }

    return (
        <div className="daily-forecast-card">
            <div className="forecast-container">
                {daysList.map(({ dayName, isSelected, date }, index) => {
                    const dayData = forecast[index] || {};
                    
                    return (
                        <div 
                            key={date} 
                            className={`forecast-day ${isSelected ? 'selected-day' : ''}`}
                        >
                            <div className="day-name">{dayName}</div>
                            <div className="temp-range">
                                {dayData.temperature !== undefined ? (
                                    `${dayData.temperature}°C`
                                ) : (
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