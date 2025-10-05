import React, { useState, useEffect, useRef } from 'react';
import './TodayWeatherSection.css';
import { useApp } from '../../../contexts/AppContext';
import MetricsCard from '../MetricsCard/MetricsCard';
import { geocodeLocation } from '../../../utils/api';

const TodayWeatherSection: React.FC = () => {
  const { state, setSelectedDate, setSelectedTime, setLocation } = useApp();
  const { weatherData, location, selectedDate, selectedTime } = state;

  
  // Estados para busca de localização
  const [locationQuery, setLocationQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!selectedDate) {
      const today = new Date().toISOString().split('T')[0];
      setSelectedDate(today);
    }
  }, [selectedDate, setSelectedDate]);

  // Fecha o dropdown quando clicar fora
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  // Busca de localização
  const handleLocationSearch = async (query: string) => {
    setLocationQuery(query);

    
    if (!query.trim()) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    setIsSearching(true);
    setShowDropdown(true);

    
    try {
      const results = await geocodeLocation(query);
      setSearchResults(results);
    } catch (error) {
      console.error('Erro na busca:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleLocationSelect = (selectedLocation: any) => {
    setLocation({
      latitude: selectedLocation.latitude,
      longitude: selectedLocation.longitude,
      city: selectedLocation.city,
      state: selectedLocation.state,
      country: selectedLocation.country,
    });
    setLocationQuery('');
    setSearchResults([]);
    setShowDropdown(false);
  };

  const handleTimeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    if (value === '') {
      // Horário não definido - mostra min/max nas previsões
      setSelectedTime(null);
    } else {
      const hour = parseInt(value);
      if (!isNaN(hour)) {
        setSelectedTime({
          hour,
          formatted: `${hour.toString().padStart(2, '0')}:00`
        });
      }
    }
  };

  const handleDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedDate(event.target.value);
  };

  // Gera opções de horário (inclui opção para "todos os horários")
  const timeOptions = [
    { hour: undefined, formatted: 'All Day' },
    ...Array.from({ length: 24 }, (_, i) => ({
      hour: i,
      formatted: `${i.toString().padStart(2, '0')}:00`
    }))
  ];

  if (!weatherData) {
    return (
      <div className="today-weather-section">
        <div className="section-header">
          <h2 className="section-title">Weather Today</h2>
          <div className="weather-controls">
            <div className="control-group">
              <select className="control-select location-select">
                <option>Select Location</option>
              </select>
            </div>
            <div className="control-group">
              <select className="control-select time-select">
                <option>Select Time</option>
              </select>
            </div>
            <div className="control-group">
              <input type="date" className="control-select date-select" />
            </div>
          </div>
        </div>
        <div className="metrics-loading">Loading weather data...</div>
      </div>
    );
  }

  // Dados baseados na imagem de design
  const metricsData = [
    {
      imageSrc: '/sun.png',
      value: '28 °C temperature',
      label: '',
      variant: 'temperature' as const
    },
    {
      imageSrc: '/calor-extremo.png',
      value: '2% chance of extreme heat',
      label: '',
      variant: 'extreme-heat' as const
    },
    {
      imageSrc: '/vento-folha.png',
      value: '47% chance of strong winds',
      label: '',
      variant: 'wind' as const
    },
    {
      imageSrc: '/chuva.png',
      value: '7% chance of humidity',
      label: '',
      variant: 'humidity' as const
    },
    {
      imageSrc: '/nuvem.png',
      value: '27% chance of overcast',
      label: '',
      variant: 'fog' as const
    },
    {
      imageSrc: '/chuva-nuvem.png',
      value: '15% chance of rain',
      label: '',
      variant: 'rain' as const
    },
    {
      imageSrc: '/raios.png',
      value: '3% chance of storm',
      label: '',
      variant: 'storm' as const
    },
    {
      imageSrc: '/neve.png',
      value: '0% chance of snow',
      label: '',
      variant: 'snow' as const
    }
  ];
  return (
    <div className="today-weather-section">
      <div className="section-header">
        <div className="header-left">
          <h2 className="section-title">Weather Today</h2>
          <div className="location-display">
            <span className="location-pin">📍</span>
            <span className="location-text">{location.city} - {location.state}</span>
          </div>
        </div>

        <div className="weather-controls">
          <div className="control-group location-search-group" ref={dropdownRef}>
            <div className="location-search-container">
              <input
                type="text"
                placeholder="Select a Location"
                value={locationQuery}
                onChange={(e) => handleLocationSearch(e.target.value)}
                className="control-select location-search-input"
              />

              {showDropdown && (
                <div className="location-dropdown">
                  {isSearching && (
                    <div className="search-loading">Searching...</div>
                  )}

                  {!isSearching && searchResults.length > 0 && (
                    <>
                      {searchResults.map((result, index) => (
                        <div
                          key={index}
                          className="location-option"
                          onClick={() => handleLocationSelect(result)}
                        >
                          <span className="location-icon">📍</span>
                          <span className="location-name">
                            {result.city}, {result.state}
                          </span>
                        </div>
                      ))}
                    </>
                  )}

                  {!isSearching && searchResults.length === 0 && locationQuery.trim() && (
                    <div className="no-results">No results found</div>
                  )}
                </div>
              )}
            </div>
          </div>

          <div className="control-group">
            <select
              className="control-select time-select"
              value={selectedTime?.hour ?? ''}
              onChange={handleTimeChange}
            >
              {timeOptions.map(({ hour, formatted }, index) => (
                <option key={index} value={hour ?? ''}>
                  {formatted}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <input
              type="date"
              className="control-select date-select"
              value={selectedDate}
              onChange={handleDateChange}
            />
          </div>
        </div>
      </div>

      <div className="metrics-grid">
        {metricsData.map((metric, index) => (
          <MetricsCard
            key={index}
            imageSrc={metric.imageSrc}
            value={metric.value}
            label={metric.label}
            variant={metric.variant}
          />
        ))}
      </div>
    </div>
  );
};

export default TodayWeatherSection;
