import React, { useEffect } from 'react';
import './MapCard.css';
import { useApp } from '../../../contexts/AppContext';
import { MapCardSkeleton } from '../../common/SkeletonLoader';

const MapCard: React.FC = () => {
  const { state } = useApp();
  const { location } = state;

  const generateMapUrl = () => {
    const { latitude, longitude } = location;
    const margin = 0.05;
    const bbox = [
      longitude - margin,
      latitude - margin,
      longitude + margin,
      latitude + margin
    ].join('%2C');
    return `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${latitude}%2C${longitude}`;
  };

  useEffect(() => {
  }, [location]);

  if (state.isLoading) {
    return <MapCardSkeleton />;
  }

  return (
    <div className="map-card">
      <div className="card-header map-header">
        <span className="header-title">Location</span>
        <span className="header-location">{location.city}, {location.state}</span>
      </div>

      <div className="map-container">
        <iframe
          src={generateMapUrl()}
          width="100%"
          height="100%"
          style={{ border: 0, borderRadius: '8px' }}
          title={`Mapa de ${location.city}`}
        ></iframe>
      </div>
    </div>
  );
};

export default MapCard;
