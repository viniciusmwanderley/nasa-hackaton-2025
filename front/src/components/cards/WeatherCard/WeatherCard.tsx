import React from 'react';
import './WeatherCard.css';
import { useApp } from '../../../contexts/AppContext';
import { WeatherCardSkeleton } from '../../common/SkeletonLoader';

const getWeatherEmoji = (condition: string) => {
  switch (condition) {
    case 'hot':
      return '☀️';
    case 'cold':
      return '❄️';
    case 'windy':
      return '💨';
    case 'wet':
      return '🌧️';
    default:
      return '☀️';
  }
};

const getWeatherImage = (condition: string) => {
  switch (condition) {
    case 'hot':
      return '/renewable.png';
    case 'cold':
      return '/soando.png'; 
    case 'windy':
      return '/soando.png'; 
    case 'wet':
      return '/soando.png'; 
    default:
      return '/soando.png';
  }
};

const WeatherCard: React.FC = () => {
    const { state } = useApp();
    const { weatherData, location, isLoading } = state;

    if (isLoading) {
        return <WeatherCardSkeleton />;
    }

    if (!weatherData && !isLoading) {
        return null;
    }

    if (!weatherData) {
        return null;
    }

    return (
        <div className="weather-card">
            <div className="weather-text-content">
                <h2 className="weather-title">Clima Hoje</h2>
                <p className="weather-subtitle">
                    {weatherData.description}
                </p>
                
                <div className="weather-main-info">
                    <p className="temperature">
                        <span role="img" aria-label="weather">
                            {getWeatherEmoji(weatherData.condition)}
                        </span> {weatherData.temperature}°C
                    </p>
                    <p className="rain-chance">
                        <span role="img" aria-label="rain">🌧️</span> {weatherData.rainChance}% de chances de chover
                    </p>
                    <p className="location">
                        <span role="img" aria-label="pin">📍</span> {location.city}, {location.state}
                    </p>
                </div>

            </div>
            
            <div className="weather-illustration">
                <img 
                    src={getWeatherImage(weatherData.condition)}
                    alt={`Ilustração para condição: ${weatherData.condition}`}
                />
            </div>
        </div>
    );
};

export default WeatherCard;