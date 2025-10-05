import React from 'react';
import './CalendarCard.css';
import { useApp } from '../../../contexts/AppContext';

const CalendarCard: React.FC = () => {
    const { state, setSelectedDate, setSelectedTime, updateCalendarMonth } = useApp();
    const { calendar, selectedDate } = state;

    const daysOfWeek = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];

    const generateCalendarDays = (year: number, month: number) => {
        const firstDay = new Date(year, month, 1);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay()); 
        
        const days = [];
        const current = new Date(startDate);
        
        for (let i = 0; i < 42; i++) {
            const isCurrentMonth = current.getMonth() === month;
            const dateString = current.toISOString().split('T')[0];
            
            days.push({
                day: current.getDate(),
                dateString,
                isCurrentMonth,
                isToday: dateString === new Date().toISOString().split('T')[0],
                isSelected: dateString === selectedDate
            });
            
            current.setDate(current.getDate() + 1);
        }
        
        return days;
    };

    const calendarDays = generateCalendarDays(calendar.currentYear, calendar.currentMonth);
    
    const goToPreviousMonth = () => {
        const newMonth = calendar.currentMonth === 0 ? 11 : calendar.currentMonth - 1;
        const newYear = calendar.currentMonth === 0 ? calendar.currentYear - 1 : calendar.currentYear;
        updateCalendarMonth(newMonth, newYear);
    };

    const goToNextMonth = () => {
        const newMonth = calendar.currentMonth === 11 ? 0 : calendar.currentMonth + 1;
        const newYear = calendar.currentMonth === 11 ? calendar.currentYear + 1 : calendar.currentYear;
        updateCalendarMonth(newMonth, newYear);
    };

    const handleDateClick = async (dateString: string) => {
        await setSelectedDate(dateString);
    };

    return (
        <div className="calendar-card">
            
            <div className="calendar-month-controls">
                <button className="arrow-btn" onClick={goToPreviousMonth}>&lt;</button>
                <span className="month-year">
                    {monthNames[calendar.currentMonth]} {calendar.currentYear}
                </span>
                <button className="arrow-btn" onClick={goToNextMonth}>&gt;</button>
            </div>

            <div className="calendar-grid">
                {daysOfWeek.map(day => (
                    <div key={day} className="day-name">{day}</div>
                ))}

                {calendarDays.map((dayInfo, index) => (
                    <div 
                        key={index} 
                        className={`day-number 
                            ${!dayInfo.isCurrentMonth ? 'is-other-month' : ''} 
                            ${dayInfo.isToday ? 'is-today' : ''} 
                            ${dayInfo.isSelected ? 'is-selected' : ''}
                            ${dayInfo.isCurrentMonth ? 'is-clickable' : ''}
                        `}
                        onClick={() => dayInfo.isCurrentMonth && handleDateClick(dayInfo.dateString)}
                    >
                        {dayInfo.day}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default CalendarCard;