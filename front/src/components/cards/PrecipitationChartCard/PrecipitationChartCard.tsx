import React from 'react';
import './PrecipitationChartCard.css';

const PrecipitationChartCard: React.FC = () => {

    // Dados do gráfico baseados na captura de tela
    const weeklyPrecipitation = [
        { day: 'S', value: 90 },
        { day: 'T', value: 110 },
        { day: 'Q', value: 140 },
        { day: 'Q', value: 180 },
        { day: 'S', value: 190 },
        { day: 'S', value: 180 },
        { day: 'D', value: 170 },
    ];

    return (
        <div className="precipitation-card">
            <div className="card-header">
                <span className="header-title">Precipitações</span>
                <div className="header-location-wrapper">
                    <span className="header-location">João Pessoa, PB</span>
                    <div className="header-location-arrow">▼</div>
                </div>
            </div>

            <div className="chart-area">
                <div className="y-axis">
                    <div className="y-axis-tick"><span>180</span></div>
                    <div className="y-axis-tick"><span>160</span></div>
                    <div className="y-axis-tick"><span>140</span></div>
                    <div className="y-axis-tick"><span>120</span></div>
                    <div className="y-axis-tick"><span>100</span></div>
                    <div className="y-axis-tick"><span>80</span></div>
                    <div className="y-axis-tick"><span>60</span></div>
                    <div className="y-axis-tick"><span>40</span></div>
                    <div className="y-axis-tick"><span>20</span></div>
                    <div className="y-axis-tick"><span>10</span></div>
                </div>

                <div className="chart-bars">
                    {weeklyPrecipitation.map((data, index) => {
                        const normalizedHeight = (data.value / 200) * 100; // normaliza para 200mm max
                        return (
                            <div key={index} className="bar-container">
                                <div
                                    className="bar"
                                    style={{ height: `${normalizedHeight}%` }}
                                    title={`${data.day}: ${data.value}mm`}
                                ></div>
                                <div className="x-axis-label">{data.day}</div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

export default PrecipitationChartCard;
