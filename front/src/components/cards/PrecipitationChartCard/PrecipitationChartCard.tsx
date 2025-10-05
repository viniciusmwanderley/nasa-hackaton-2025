import React from 'react';
import { BarChart, Bar, ResponsiveContainer, YAxis, XAxis, Cell, Tooltip } from 'recharts';
import { useApp } from '../../../contexts/AppContext';
import { PrecipitationChartSkeleton } from '../../common/SkeletonLoader';
import './PrecipitationChartCard.css';

const PrecipitationChartCard: React.FC = () => {
    const { state } = useApp();

    const getWeeklyPrecipitation = () => {
        const selectedDateObj = new Date(state.selectedDate + 'T00:00:00');
        const dayLabels = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
        const precipitationData = [];
        
        for (let i = -3; i <= 3; i++) {
            const currentDate = new Date(selectedDateObj);
            currentDate.setDate(selectedDateObj.getDate() + i);
            const dayLabel = dayLabels[currentDate.getDay()];
            const isSelected = i === 0;
            const dateString = currentDate.toISOString().split('T')[0];
            
            const apiData = state.precipitationData.find(data => data.date === dateString);
            const value = apiData ? apiData.value : 0;
            
            precipitationData.push({
                day: dayLabel,
                value: value,
                isSelected: isSelected,
                date: dateString
            });
        }
        
        return precipitationData;
    };

    const weeklyPrecipitation = getWeeklyPrecipitation();

    const values = weeklyPrecipitation.map(item => item.value);
    const maxValue = Math.max(...values);
    
    let yAxisMax = maxValue * 1.2; 
    
    if (yAxisMax <= 1) {
        yAxisMax = Math.ceil(yAxisMax * 10) / 10; 
    } else if (yAxisMax <= 10) {
        yAxisMax = Math.ceil(yAxisMax); 
    } else {
        yAxisMax = Math.ceil(yAxisMax / 5) * 5; 
    }
    
    const yAxisDomain = [0, Math.max(yAxisMax, 1)];

    if (state.isLoading) {
        return <PrecipitationChartSkeleton />;
    }

    return (
        <div className="precipitation-card">
            <div className="card-header">
                <span className="header-title">Precipitations (mm)</span>
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
                            domain={yAxisDomain}
                            tickCount={6}
                            tickFormatter={(value) => value < 1 ? `${value.toFixed(1)}` : `${Math.round(value)}`}
                            label={{ value: 'mm', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip 
                            formatter={(value: number) => [`${value.toFixed(2)} mm`]}
                            labelFormatter={(label, payload) => {
                                if (payload && payload.length > 0) {
                                    const data = payload[0].payload;
                                    const date = new Date(data.date);
                                    const formattedDate = date.toLocaleDateString('pt-BR', {
                                        day: '2-digit',
                                        month: '2-digit'
                                    });
                                    return `${formattedDate}`;
                                }
                                return label;
                            }}
                            contentStyle={{
                                backgroundColor: 'white',
                                border: '1px solid #e0e0e0',
                                borderRadius: '4px',
                                color: '#333',
                                fontSize: '12px',
                                padding: '6px 8px',
                                boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                            }}
                        />
                        <Bar 
                            dataKey="value" 
                            radius={[4, 4, 0, 0]}
                            barSize={12}
                        >
                            {weeklyPrecipitation.map((entry, index) => (
                                <Cell 
                                    key={`cell-${index}`} 
                                    fill={entry.isSelected ? '#FF6B35' : '#3B82F6'} 
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
