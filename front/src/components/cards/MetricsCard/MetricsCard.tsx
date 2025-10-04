import React from 'react';
import './MetricsCard.css';

interface MetricCardProps {
  imageSrc: string;
  value: string;
  label: string;
  variant: 'temperature' | 'extreme-heat' | 'wind' | 'humidity' | 'fog' | 'rain' | 'storm' | 'snow';
  className?: string; // Permitir classes personalizadas
}

const MetricsCard: React.FC<MetricCardProps> = ({ imageSrc, value, label, variant, className }) => {
  return (
    <div className={`metrics-card metrics-card--${variant} ${className || ''}`}>
      <div className="metrics-card__icon">
        <img src={imageSrc} alt={label} className="metrics-card__icon-image" />
      </div>
      <div className="metrics-card__content">
        <div className="metrics-card__value">{value}</div>
        <div className="metrics-card__label">{label}</div>
      </div>
    </div>
  );
};

export default MetricsCard;
