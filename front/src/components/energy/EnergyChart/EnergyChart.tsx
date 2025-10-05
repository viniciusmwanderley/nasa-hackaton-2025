import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';
import './EnergyChart.css';

interface EnergyChartProps {
    type: 'solar' | 'eolica';
    title: string;
}

const EnergyChart: React.FC<EnergyChartProps> = ({ type, title }) => {
    const solarData = [
        { city: 'João Pessoa', value: 250, shortName: 'João\nPessoa' },
        { city: 'São José de Sabugi', value: 580, shortName: 'São José\nde Sabugi' },
        { city: 'Areia do Breianas', value: 280, shortName: 'Areia do\nBreianas' },
        { city: 'São Mamede', value: 480, shortName: 'São\nMamede' },
        { city: 'Santa Luzia', value: 620, shortName: 'Santa\nLuzia' }
    ];

    const eolicaData = [
        { city: 'João Pessoa', value: 300, shortName: 'João\nPessoa' },
        { city: 'São José de Sabugi', value: 680, shortName: 'São José\nde Sabugi' },
        { city: 'Areia do Breianas', value: 320, shortName: 'Areia do\nBreianas' },
        { city: 'São Mamede', value: 460, shortName: 'São\nMamede' },
        { city: 'Santa Luzia', value: 420, shortName: 'Santa\nLuzia' }
    ];

    const data = type === 'solar' ? solarData : eolicaData;
    const color = type === 'solar' ? '#ff9500' : '#007bff';

    const CustomXAxisTick = (props: any) => {
        const { x, y, payload } = props;
        const lines = payload.value.split('\n');
        
        return (
            <g transform={`translate(${x},${y})`}>
                {lines.map((line: string, index: number) => (
                    <text
                        key={index}
                        x={0}
                        y={index * 12 + 10}
                        dy={0}
                        textAnchor="middle"
                        fill="#666"
                        fontSize="11"
                    >
                        {line}
                    </text>
                ))}
            </g>
        );
    };

    return (
        <div className="energy-chart">
            <h3 className="chart-title">{title}</h3>
            <div className="recharts-container">
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart
                        data={data}
                        margin={{
                            top: 20,
                            right: 30,
                            left: 20,
                            bottom: 60,
                        }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis 
                            dataKey="shortName"
                            tick={<CustomXAxisTick />}
                            height={60}
                            interval={0}
                        />
                        <YAxis 
                            domain={[0, 700]}
                            tick={{ fontSize: 12, fill: '#666' }}
                        />
                        <Bar 
                            dataKey="value" 
                            fill={color}
                            radius={[4, 4, 0, 0]}
                        />
                    </BarChart>
                </ResponsiveContainer>
            </div>
            <div className="chart-footer">
                <span className="cities-label">
                    Cidades com maior potencial para produção de{' '}
                    <span style={{ color }}>{type === 'solar' ? 'energia solar' : 'energia eólica'}</span>
                </span>
            </div>
        </div>
    );
};

export default EnergyChart;
