import React from 'react';
import { BarChart, Bar, ResponsiveContainer, YAxis, XAxis, Cell } from 'recharts';
import { useApp } from '../../../contexts/AppContext';
import './PrecipitationChartCard.css';

const PrecipitationChartCard: React.FC = () => {
    const { state } = useApp();

    // Dados do gráfico baseados na captura de tela
    const weeklyPrecipitation = [
        { day: 'M', value: 90 },
        { day: 'T', value: 90 },
        { day: 'W', value: 90 },
        { day: 'T', value: 180 },
        { day: 'F', value: 90 },
        { day: 'S', value: 90 },
        { day: 'S', value: 90 },
    ];

    return (
        <div className="precipitation-card">
            <div className="card-header">
                <span className="header-title">Precipitations</span>
                <div className="header-location-wrapper">
                    <span className="header-location">{`${state.location.city}, ${state.location.state}`}</span>
                    <span className="header-location-arrow">▼</span>
                </div>
            </div>

            <div className="chart-container">
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart
                        data={weeklyPrecipitation}
                        margin={{
                            top: 20,
                            right: 30,
                            left: 20,
                            bottom: 5,
                        }}
                    >
                        <XAxis 
                            dataKey="day" 
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 12, fill: '#666' }}
                        />
                        <YAxis 
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 12, fill: '#666' }}
                            domain={[0, 200]}
                            ticks={[10, 20, 40, 60, 80, 100, 120, 140, 160, 180]}
                        />
                        <Bar 
                            dataKey="value" 
                            radius={[4, 4, 0, 0]}
                            barSize={12}
                        >
                            {weeklyPrecipitation.map((entry, index) => (
                                <Cell 
                                    key={`cell-${index}`} 
                                    fill={entry.value === 180 ? '#3B82F6' : '#1E40AF'} 
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default PrecipitationChartCard;
