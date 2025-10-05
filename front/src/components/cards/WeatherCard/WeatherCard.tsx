import React from 'react';
import './WeatherCard.css';
import { useApp } from '../../../contexts/AppContext';
import { WeatherCardSkeleton } from '../../common/SkeletonLoader';

// Função para obter emoji baseado na condição
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

// Função para obter imagem baseada na condição
const getWeatherImage = (condition: string) => {
  switch (condition) {
    case 'hot':
      return '/renewable.png';
    case 'cold':
      return '/soando.png'; // TODO: adicionar imagem para frio
    case 'windy':
      return '/soando.png'; // TODO: adicionar imagem para vento
    case 'wet':
      return '/soando.png'; // TODO: adicionar imagem para chuva
    default:
      return '/soando.png';
  }
};

const WeatherCard: React.FC = () => {
    const { state } = useApp();
    const { weatherData, location, isLoading } = state;

    // Se está carregando, mostra skeleton
    if (isLoading) {
        return <WeatherCardSkeleton />;
    }

    // Se não há dados meteorológicos e não está carregando, não renderiza
    if (!weatherData && !isLoading) {
        return null;
    }

    // Se não há weatherData mas não está em loading, não renderiza o conteúdo
    if (!weatherData) {
        return null;
    }

    return (
        <div className="weather-card">
            {/* Componente 1: TODO o conteúdo de texto */}
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
            
            {/* Componente 2: Apenas a imagem */}
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