import React from 'react';
import './CityRanking.css';

interface CityRankingProps {
    energyType: 'solar' | 'eolica';
}

const CityRanking: React.FC<CityRankingProps> = ({ energyType }) => {
    const solarCities = [
        { position: 1, name: 'Santa Luzia', power: '1000W' },
        { position: 2, name: 'Coremas', power: '900W' },
        { position: 3, name: 'Patos', power: '800W' },
        { position: 4, name: 'São Mamede', power: '700W' },
        { position: 5, name: 'Souza', power: '600W' }
    ];

    const eolicaCities = [
        { position: 1, name: 'Santa Luzia', power: '1000W' },
        { position: 2, name: 'Coremas', power: '900W' },
        { position: 3, name: 'Patos', power: '800W' },
        { position: 4, name: 'São Mamede', power: '700W' },
        { position: 5, name: 'Souza', power: '600W' }
    ];

    const cities = energyType === 'solar' ? solarCities : eolicaCities;
    const color = energyType === 'solar' ? '#ff9500' : '#007bff';
    const energyLabel = energyType === 'solar' ? 'energia solar' : 'energia eólica';

    return (
        <div className="city-ranking">
            <div className="ranking-header">
                <h3>Cidades com maior potencial para produção de</h3>
                <h3 style={{ color }}>{energyLabel}</h3>
            </div>
            
            <div className="ranking-list">
                {cities.map((city) => (
                    <div key={`${energyType}-${city.position}`} className="ranking-item">
                        <div className="position-circle" style={{ backgroundColor: color }}>
                            {city.position}°
                        </div>
                        <div className="city-info">
                            <span className="city-name">{city.name}</span>
                            <span className="city-power">{city.power}</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default CityRanking;
