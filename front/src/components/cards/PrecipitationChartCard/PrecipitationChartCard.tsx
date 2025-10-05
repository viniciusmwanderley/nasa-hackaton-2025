import React from 'react';
import { BarChart, Bar, ResponsiveContainer, YAxis, XAxis, Cell, Tooltip } from 'recharts';
import { useApp } from '../../../contexts/AppContext';
import { PrecipitationChartSkeleton } from '../../common/SkeletonLoader';
import './PrecipitationChartCard.css';

const PrecipitationChartCard: React.FC = () => {
    const { state } = useApp();

    // Gera dados de precipitação baseado na data selecionada (centro) com 3 antes e 3 depois
    const getWeeklyPrecipitation = () => {
        const selectedDateObj = new Date(state.selectedDate + 'T00:00:00');
        const dayLabels = ['S', 'M', 'T', 'W', 'T', 'F', 'S']; // Dom, Seg, Ter, Qua, Qui, Sex, Sab
        const precipitationData = [];
        
        // 3 dias antes, dia selecionado, 3 dias depois
        for (let i = -3; i <= 3; i++) {
            const currentDate = new Date(selectedDateObj);
            currentDate.setDate(selectedDateObj.getDate() + i);
            const dayLabel = dayLabels[currentDate.getDay()];
            const isSelected = i === 0;
            const dateString = currentDate.toISOString().split('T')[0];
            
            // Busca dados correspondentes da API por data
            const apiData = state.precipitationData.find(data => data.date === dateString);
            // Os dados já vêm em mm da API (PRECTOTCORR) - valores exatos da NASA
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

    // Calcula escala dinâmica baseada nos valores reais
    const values = weeklyPrecipitation.map(item => item.value);
    const maxValue = Math.max(...values);
    
    // Define domínio do eixo Y com base nos dados reais para uma escala mais regular
    let yAxisMax = maxValue * 1.2; // 20% de margem acima do máximo
    
    // Arredonda para números mais limpos na escala
    if (yAxisMax <= 1) {
        yAxisMax = Math.ceil(yAxisMax * 10) / 10; // Arredonda para 0.1
    } else if (yAxisMax <= 10) {
        yAxisMax = Math.ceil(yAxisMax); // Arredonda para inteiro
    } else {
        yAxisMax = Math.ceil(yAxisMax / 5) * 5; // Arredonda para múltiplo de 5
    }
    
    const yAxisDomain = [0, Math.max(yAxisMax, 1)];

    // Se está carregando, mostra skeleton
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
                                    fill={entry.isSelected ? '#FF6B35' : '#3B82F6'} // Destaca o dia selecionado
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
