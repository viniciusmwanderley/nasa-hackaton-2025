import React, { useState, useEffect, useRef, useCallback } from 'react';
import './TodayWeatherSection.css';
import { useApp } from '../../../contexts/AppContext';
import { useFilter } from '../../../contexts/FilterContext';
import MetricsCard from '../MetricsCard/MetricsCard';
import { TodayWeatherSkeleton } from '../../common/SkeletonLoader';
import { geocodeLocation } from '../../../utils/api';
import type { TimeSelection } from '../../../types';

const TodayWeatherSection: React.FC = () => {
  const { state, setSelectedDate, setSelectedTime, setLocation, analyzeWeather } = useApp();
  const { weatherData, location, selectedDate, selectedTime } = state;
  const { localDate, setLocalDate } = useFilter();

  // Local state for time and location (separate from global state)  
  const [localTime, setLocalTime] = useState<TimeSelection | null>(null); // Default to "All Day"
  const [localLocation, setLocalLocation] = useState(location);
  
  const [locationQuery, setLocationQuery] = useState(`${location.city}, ${location.state}`);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Flag to track if user has manually changed local values
  const [hasUserChangedDate, setHasUserChangedDate] = useState(() => {
    return localStorage.getItem('userChangedDate') === 'true';
  });
  const [hasUserChangedTime, setHasUserChangedTime] = useState(() => {
    return localStorage.getItem('userChangedTime') === 'true';
  });
  const [hasUserChangedLocation, setHasUserChangedLocation] = useState(() => {
    return localStorage.getItem('userChangedLocation') === 'true';
  });

  useEffect(() => {
    if (!selectedDate) {
      const today = new Date().toISOString().split('T')[0];
      setSelectedDate(today); 
    }
    
    // Only sync local states with global state if user hasn't manually changed them
    if (!hasUserChangedDate) {
      setLocalDate(selectedDate);
    }
    
    // Only sync localTime if selectedTime is not null and user hasn't changed it manually
    if (selectedTime !== null && !hasUserChangedTime) {
      setLocalTime(selectedTime);
    }
    
    // Only sync location if user hasn't manually changed it
    if (!hasUserChangedLocation) {
      setLocalLocation(location);
      setLocationQuery(`${location.city}, ${location.state}`);
    }
  }, [selectedDate, selectedTime, location, setSelectedDate, setLocalDate, hasUserChangedDate, hasUserChangedTime, hasUserChangedLocation]);

  // Listen for changes in localStorage to sync flags across components
  useEffect(() => {
    const checkLocalStorage = () => {
      const dateChanged = localStorage.getItem('userChangedDate') === 'true';
      const timeChanged = localStorage.getItem('userChangedTime') === 'true';
      const locationChanged = localStorage.getItem('userChangedLocation') === 'true';
      
      if (dateChanged !== hasUserChangedDate) {
        setHasUserChangedDate(dateChanged);
      }
      if (timeChanged !== hasUserChangedTime) {
        setHasUserChangedTime(timeChanged);
      }
      if (locationChanged !== hasUserChangedLocation) {
        setHasUserChangedLocation(locationChanged);
      }
    };

    // Check immediately and set up an interval to check periodically
    checkLocalStorage();
    const interval = setInterval(checkLocalStorage, 100);

    return () => clearInterval(interval);
  }, [hasUserChangedDate, hasUserChangedTime, hasUserChangedLocation]);

  // Close dropdown when clicking outside
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
      console.error('Error searching for location:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleLocationSelect = (selectedLocation: any) => {
    const newLocation = {
      latitude: selectedLocation.latitude,
      longitude: selectedLocation.longitude,
      city: selectedLocation.city,
      state: selectedLocation.state,
      country: selectedLocation.country,
    };
    setLocalLocation(newLocation);
    setLocationQuery(`${selectedLocation.city}, ${selectedLocation.state}`);
    setSearchResults([]);
    setShowDropdown(false);
    setHasUserChangedLocation(true);
    localStorage.setItem('userChangedLocation', 'true');
  };

    const handleTimeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value;
    
    if (value === '') {
      // "All Day" selected
      setLocalTime(null);
    } else {
      const hour = parseInt(value, 10);
      if (!isNaN(hour)) {
        setLocalTime({
          hour,
          formatted: `${hour.toString().padStart(2, '0')}:00`
        });
      }
    }
    setHasUserChangedTime(true);
    localStorage.setItem('userChangedTime', 'true');
  };

  const handleDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setLocalDate(event.target.value);
    setHasUserChangedDate(true);
    localStorage.setItem('userChangedDate', 'true');
  };

  const handleAnalyze = useCallback(async () => {
    // Update the global state with local values
    setSelectedDate(localDate);
    setSelectedTime(localTime);
    setLocation(localLocation);
    
    // Reset the flags after analyzing, so the component can sync with new results
    setHasUserChangedDate(false);
    setHasUserChangedTime(false);
    setHasUserChangedLocation(false);
    localStorage.removeItem('userChangedDate');
    localStorage.removeItem('userChangedTime');
    localStorage.removeItem('userChangedLocation');
    
    // Trigger the analysis with the local values directly
    await analyzeWeather(localLocation, localDate, localTime);
  }, [localLocation, localDate, localTime, analyzeWeather, setSelectedDate, setSelectedTime, setLocation]);

  const timeOptions = [
    { hour: undefined, formatted: 'All Day' },
    ...Array.from({ length: 24 }, (_, i) => ({
      hour: i,
      formatted: `${i.toString().padStart(2, '0')}:00`
    }))
  ];

  // Always show the component - don't return null

  const { apiData } = state;
  
  const metricsData = [
    {
      imageSrc: '/sun.png',
      value: `${weatherData?.temperature}°C temperature`,
      label: '',
      variant: 'temperature' as const
    },
    {
      imageSrc: '/calor-extremo.png',
      value: apiData?.classifications ? `${Math.round(apiData.classifications.very_hot_temp_percentile)}% chance of extreme heat` : 'Select filters and analyze for data',
      label: '',
      variant: 'extreme-heat' as const
    },
    {
      imageSrc: '/vento-folha.png',
      value: apiData?.classifications ? `${Math.round(apiData.classifications.very_windy_percentile )}% chance of strong winds` : 'Select filters and analyze for data',
      label: '',
      variant: 'wind' as const
    },
    {
      imageSrc: '/chuva.png',
      value: apiData?.selectedDayData?.parameters?.RH2M?.value ? `${Math.round(apiData.selectedDayData.parameters.RH2M.value)}% humidity` : 'Select filters and analyze for data',
      label: '',
      variant: 'humidity' as const
    },
    {
      imageSrc: '/nuvem.png',
      value: apiData?.selectedDayData?.parameters?.CLOUD_AMT?.value ? `${Math.round(apiData.selectedDayData.parameters.CLOUD_AMT.value)}% overcast` : 'Select filters and analyze for data',
      label: '',
      variant: 'fog' as const
    },
    {
      imageSrc: '/chuva-nuvem.png',
      value: `${weatherData?.rainChance}% chance of rain`,
      label: '',
      variant: 'rain' as const
    },
    {
      imageSrc: '/raios.png',
      value: apiData?.classifications ? `${Math.round((apiData.classifications.very_wet_probability ) * 100)}% chance of storm` : 'Select filters and analyze for data',
      label: '',
      variant: 'storm' as const
    },
    {
      imageSrc: '/neve.png',
      value: apiData?.classifications ? `${Math.round((apiData.classifications.very_snowy_probability ) * 100)}% chance of snow` : 'Select filters and analyze for data',
      label: '',
      variant: 'snow' as const
    }
  ];

  if (state.isLoading) {
    return <TodayWeatherSkeleton />;
  }

  return (
    <div className="today-weather-section">
      <div className="section-header">
        <div className="header-left">
          <h2 className="section-title">Weather Info</h2>
          <div className="location-display">
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
                disabled={state.isLoading}
              />

              {showDropdown && (
                <div className="location-dropdown">
                  {isSearching && (
                    <div className="search-loading">
                      <div style={{
                        height: '12px',
                        backgroundColor: '#e0e0e0',
                        borderRadius: '6px',
                        animation: 'shimmer 1.5s ease-in-out infinite',
                        background: 'linear-gradient(90deg, #e0e0e0 25%, #f0f0f0 50%, #e0e0e0 75%)',
                        backgroundSize: '200% 100%'
                      }}></div>
                    </div>
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
              value={localTime?.hour ?? ''}
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
              value={localDate}
              onChange={handleDateChange}
            />
          </div>

          <div className="control-group">
            <button
              className="control-button analyze-button"
              onClick={handleAnalyze}
              disabled={state.isLoading}
            >
              {state.isLoading ? 'Analyzing...' : 'Analyze'}
            </button>
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
