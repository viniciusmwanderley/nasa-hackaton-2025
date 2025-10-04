import React, { useState } from 'react';
import './MapCard.css';
import { useApp } from '../../../contexts/AppContext';
import type { Location } from '../../../types';

const MapCard: React.FC = () => {
    const { state, setLocation } = useApp();
    const { location } = state;
    const [isSearching, setIsSearching] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    // Gera URL do mapa baseada na localização atual
    const generateMapUrl = () => {
        const { latitude, longitude } = location;
        // Calcula bbox ao redor do ponto central (aproximadamente 0.1 graus de margem)
        const margin = 0.05;
        const bbox = [
            longitude - margin,
            latitude - margin,
            longitude + margin,
            latitude + margin
        ].join('%2C');
        
        return `https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${latitude}%2C${longitude}`;
    };

    // Simula busca de localização (futuramente integrará com geocoding API)
    const handleSearch = async () => {
        if (!searchQuery.trim()) return;
        
        setIsSearching(true);
        
        // TODO: Implementar integração com API de geocoding
        // Por enquanto, simula uma busca
        setTimeout(() => {
            // Simula algumas localizações conhecidas
            const mockLocations: { [key: string]: Location } = {
                'fortaleza': {
                    latitude: -3.7319,
                    longitude: -38.5267,
                    city: 'FORTALEZA',
                    state: 'CE',
                    country: 'Brasil'
                },
                'recife': {
                    latitude: -8.0476,
                    longitude: -34.8770,
                    city: 'RECIFE',
                    state: 'PE',
                    country: 'Brasil'
                },
                'natal': {
                    latitude: -5.7945,
                    longitude: -35.2110,
                    city: 'NATAL',
                    state: 'RN',
                    country: 'Brasil'
                },
                'joão pessoa': {
                    latitude: -7.1195,
                    longitude: -34.8473,
                    city: 'JOÃO PESSOA',
                    state: 'PB',
                    country: 'Brasil'
                }
            };

            const searchLower = searchQuery.toLowerCase();
            const foundLocation = mockLocations[searchLower];
            
            if (foundLocation) {
                setLocation(foundLocation);
                setSearchQuery('');
            } else {
                // Se não encontrar, mantém a localização atual e limpa a busca
                console.log('Localização não encontrada:', searchQuery);
            }
            
            setIsSearching(false);
        }, 1000);
    };

    const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') {
            handleSearch();
        }
    };

    return (
        <div className="map-card">
            <div className="card-header map-header">
                <span className="header-title">Local</span>
                <div className="location-search">
                    {isSearching ? (
                        <span className="header-location searching">Buscando...</span>
                    ) : (
                        <>
                            <input
                                type="text"
                                placeholder={location.city}
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyPress={handleKeyPress}
                                className="location-input"
                            />
                            <button 
                                className="search-icon" 
                                onClick={handleSearch}
                                disabled={isSearching || !searchQuery.trim()}
                            >
                                🔍
                            </button>
                        </>
                    )}
                </div>
            </div>
            
            {/* Mapa usando OpenStreetMap via iframe com localização dinâmica */}
            <div className="map-container">
                <div className="map-wrapper">
                    <iframe
                        src={generateMapUrl()}
                        width="100%"
                        height="100%"
                        style={{ border: 0, borderRadius: '8px' }}
                        title={`Mapa de ${location.city}`}
                    ></iframe>
                    <div className="map-overlay">
                        <div className="location-info">
                            <div className="location-name">
                                {location.city}, {location.state}
                            </div>
                            <div className="location-coords">
                                {location.latitude.toFixed(4)}°, {location.longitude.toFixed(4)}°
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MapCard;