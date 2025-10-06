import React from 'react';
import './CalendarCard.css';
import { useApp } from '../../../contexts/AppContext';
import { useFilter } from '../../../contexts/FilterContext';
import { getTimezoneFromLocationSync } from '../../../utils/timezone';

const CalendarCard: React.FC = () => {
    const { state, updateCalendarMonth } = useApp();
    const { calendar, location } = state;
    const { localDate, setLocalDate } = useFilter();

    const getTodayInUserTimezone = (): string => {
        const userTimezone = getTimezoneFromLocationSync(location);
        const now = new Date();
        
        const formatter = new Intl.DateTimeFormat('en-CA', {
            timeZone: userTimezone,
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        });
        
        return formatter.format(now);
    };

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
        const todayInUserTimezone = getTodayInUserTimezone();
        
        for (let i = 0; i < 42; i++) {
            const isCurrentMonth = current.getMonth() === month;
            const dateString = current.toISOString().split('T')[0];
            
            days.push({
                day: current.getDate(),
                dateString,
                isCurrentMonth,
                isToday: dateString === todayInUserTimezone,
                isSelected: dateString === localDate
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

    const handleDateClick = (dateString: string) => {
        // Only update the local date for the datepicker, don't affect other components
        setLocalDate(dateString);
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