import React from 'react';

interface SkeletonProps {
  width?: string;
  height?: string;
  borderRadius?: string;
  className?: string;
  style?: React.CSSProperties;
}

const Skeleton: React.FC<SkeletonProps> = ({ 
  width = '100%', 
  height = '20px', 
  borderRadius = '4px',
  className = '',
  style = {}
}) => (
  <div 
    className={`skeleton ${className}`}
    style={{
      width,
      height,
      borderRadius,
      background: 'linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)',
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.5s infinite',
      ...style
    }}
  />
);

export const TodayWeatherSkeleton: React.FC = () => (
  <div className="today-weather" style={{ padding: '32px', backgroundColor: 'white', borderRadius: '16px', minHeight: '300px' }}>
    <div style={{ marginBottom: '24px' }}>
      <Skeleton width="180px" height="28px" borderRadius="8px" />
    </div>
    
    <div style={{ marginBottom: '32px' }}>
      <Skeleton width="100%" height="48px" borderRadius="12px" />
    </div>
    
    <div style={{ marginBottom: '24px' }}>
      <Skeleton width="250px" height="24px" borderRadius="6px" style={{ marginBottom: '12px' }} />
      <Skeleton width="300px" height="20px" borderRadius="6px" />
    </div>
    
    <div style={{ display: 'flex', gap: '24px', marginBottom: '16px' }}>
      <Skeleton width="120px" height="32px" borderRadius="8px" />
      <Skeleton width="180px" height="20px" borderRadius="6px" />
    </div>
    
    <div>
      <Skeleton width="200px" height="20px" borderRadius="6px" />
    </div>
    
    <style>
      {`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}
    </style>
  </div>
);

export const DailyForecastSkeleton: React.FC = () => (
  <div className="daily-forecast-card">
    <div className="forecast-container">
      {[1, 2, 3, 4, 5, 6, 7].map(i => (
        <div key={i} className="forecast-day" style={{ minHeight: '100px' }}>
          <Skeleton width="40px" height="16px" borderRadius="6px" />
          <Skeleton width="60px" height="14px" borderRadius="6px" style={{ marginTop: '12px' }} />
        </div>
      ))}
    </div>
    
    <style>
      {`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}
    </style>
  </div>
);

export const PrecipitationChartSkeleton: React.FC = () => (
  <div className="precipitation-card">
    <div className="card-header">
      <Skeleton width="150px" height="20px" borderRadius="8px" />
    </div>
    
    <div className="chart-container" style={{ height: '300px', display: 'flex', alignItems: 'end', gap: '20px', padding: '20px' }}>
      {[40, 60, 80, 100, 70, 50, 30].map((height, i) => (
        <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
          <Skeleton width="100%" height={`${height}px`} borderRadius="4px 4px 0 0" />
          <Skeleton width="20px" height="12px" borderRadius="4px" />
        </div>
      ))}
    </div>
    
    <style>
      {`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}
    </style>
  </div>
);

export const MapCardSkeleton: React.FC = () => (
  <div className="map-card">
    <div className="card-header map-header">
      <Skeleton width="80px" height="16px" borderRadius="6px" />
      <Skeleton width="120px" height="16px" borderRadius="6px" />
    </div>
    
    <div style={{ height: '200px', padding: '16px' }}>
      <Skeleton width="100%" height="100%" borderRadius="8px" />
    </div>
    
    <style>
      {`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}
    </style>
  </div>
);

export const WeatherCardSkeleton: React.FC = () => (
  <div className="weather-card" style={{ padding: '24px', backgroundColor: 'white', borderRadius: '12px' }}>
    <div className="weather-text-content">
      <Skeleton width="160px" height="28px" borderRadius="8px" />
      <Skeleton width="220px" height="20px" borderRadius="6px" style={{ marginTop: '12px' }} />
      <Skeleton width="100px" height="32px" borderRadius="8px" style={{ marginTop: '16px' }} />
    </div>
    
    <style>
      {`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}
    </style>
  </div>
);

export default Skeleton;
