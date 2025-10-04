import React from 'react';
import './TodayWeatherSection.css';
import { useApp } from '../../../contexts/AppContext';
import MetricsCard from '../MetricsCard/MetricsCard';

const TodayWeatherSection: React.FC = () => {
  const { state, setSelectedDate, setSelectedTime, setLocation } = useApp();
  const { weatherData, location, selectedDate, selectedTime } = state;

  const handleLocationChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const locationKey = event.target.value;
    // TODO: Implementar mudança de localização baseada na seleção
    console.log('Mudança de local:', locationKey);
  };

  const handleTimeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const hour = parseInt(event.target.value);
    if (!isNaN(hour)) {
      setSelectedTime({
        hour,
        formatted: `${hour.toString().padStart(2, '0')}:00`
      });
    }
  };

  const handleDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedDate(event.target.value);
  };

  // Gera opções de horário (0-23)
  const timeOptions = Array.from({ length: 24 }, (_, i) => ({
    hour: i,
    formatted: `${i.toString().padStart(2, '0')}:00`
  }));

  if (!weatherData) {
    return (
      <div className="today-weather-section">
        <div className="section-header">
          <h2 className="section-title">Clima Hoje</h2>
          <div className="weather-controls">
            <div className="control-group">
              <select className="control-select location-select">
                <option>Selecione um Local</option>
              </select>
            </div>
            <div className="control-group">
              <select className="control-select time-select">
                <option>Defina um Horário</option>
              </select>
            </div>
            <div className="control-group">
              <input type="date" className="control-select date-select" />
            </div>
          </div>
        </div>
        <div className="metrics-loading">Carregando dados meteorológicos...</div>
      </div>
    );
  }

  // Dados baseados na imagem de design
  const metricsData = [
    {
      imageSrc: '/sun.png',
      value: '28 °C temperatura',
      label: '',
      variant: 'temperature' as const
    },
    {
      imageSrc: '/calor-extremo.png',
      value: '2% de chance de calor extremo',
      label: '',
      variant: 'extreme-heat' as const
    },
    {
      imageSrc: '/vento-folha.png',
      value: '47% risco de vento forte',
      label: '',
      variant: 'wind' as const
    },
    {
      imageSrc: '/chuva.png',
      value: '7% de umidade no ar',
      label: '',
      variant: 'humidity' as const
    },
    {
      imageSrc: '/nuvem.png',
      value: '27% de céu encoberto',
      label: '',
      variant: 'fog' as const
    },
    {
      imageSrc: '/chuva-nuvem.png',
      value: '15% chance de chuva',
      label: '',
      variant: 'rain' as const
    },
    {
      imageSrc: '/raios.png',
      value: '3% de chance de tempestade',
      label: '',
      variant: 'storm' as const
    },
    {
      imageSrc: '/neve.png',
      value: '0% de chance de nevar',
      label: '',
      variant: 'snow' as const
    }
  ];  return (
    <div className="today-weather-section">
      <div className="section-header">
        <div className="header-left">
          <h2 className="section-title">Clima Hoje</h2>
          <div className="location-display">
            <span className="location-pin">📍</span>
            <span className="location-text">João Pessoa - PB</span>
          </div>
        </div>
        
        <div className="weather-controls">
          <div className="control-group">
            <select 
              className="control-select location-select"
              value={location.city}
              onChange={handleLocationChange}
            >
              <option value="">Selecione um Local</option>
              <option value="joao-pessoa">João Pessoa - PB</option>
              <option value="fortaleza">Fortaleza - CE</option>
              <option value="recife">Recife - PE</option>
              <option value="natal">Natal - RN</option>
              <option value="salvador">Salvador - BA</option>
            </select>
          </div>
          
          <div className="control-group">
            <select 
              className="control-select time-select"
              value={selectedTime.hour}
              onChange={handleTimeChange}
            >
              <option value="">Defina um Horário</option>
              {timeOptions.map(({ hour, formatted }) => (
                <option key={hour} value={hour}>
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
