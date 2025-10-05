import React from 'react';
import {
    Box,
    Typography,
    Paper,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Chip,
    Container
} from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import styles from './EnergyCharts.module.css';

interface EnergyChartsProps {
    selectedMonth?: string;
    onMonthChange?: (month: string) => void;
}

const EnergyCharts: React.FC<EnergyChartsProps> = ({ 
    selectedMonth = 'janeiro', 
    onMonthChange 
}) => {
    // Mock data baseado na captura de tela
    const solarData = [
        { city: 'São Paulo', shortName: 'SP', value: 142 },
        { city: 'Rio de Janeiro', shortName: 'RJ', value: 165 },
        { city: 'Belo Horizonte', shortName: 'BH', value: 178 },
        { city: 'Salvador', shortName: 'SSA', value: 195 },
        { city: 'Fortaleza', shortName: 'FOR', value: 210 },
        { city: 'Recife', shortName: 'REC', value: 188 },
        { city: 'Brasília', shortName: 'BSB', value: 185 },
        { city: 'Curitiba', shortName: 'CWB', value: 135 },
        { city: 'Porto Alegre', shortName: 'POA', value: 128 },
        { city: 'Manaus', shortName: 'MAO', value: 155 }
    ];

    const windData = [
        { city: 'São Paulo', shortName: 'SP', value: 85 },
        { city: 'Rio de Janeiro', shortName: 'RJ', value: 102 },
        { city: 'Belo Horizonte', shortName: 'BH', value: 78 },
        { city: 'Salvador', shortName: 'SSA', value: 145 },
        { city: 'Fortaleza', shortName: 'FOR', value: 198 },
        { city: 'Recife', shortName: 'REC', value: 165 },
        { city: 'Brasília', shortName: 'BSB', value: 92 },
        { city: 'Curitiba', shortName: 'CWB', value: 115 },
        { city: 'Porto Alegre', shortName: 'POA', value: 134 },
        { city: 'Manaus', shortName: 'MAO', value: 68 }
    ];

    const solarRanking = [
        { position: 1, city: 'Fortaleza', value: '210 kWh/m²' },
        { position: 2, city: 'Salvador', value: '195 kWh/m²' },
        { position: 3, city: 'Recife', value: '188 kWh/m²' },
        { position: 4, city: 'Brasília', value: '185 kWh/m²' },
        { position: 5, city: 'Belo Horizonte', value: '178 kWh/m²' }
    ];

    const windRanking = [
        { position: 1, city: 'Fortaleza', value: '198 kWh/m²' },
        { position: 2, city: 'Recife', value: '165 kWh/m²' },
        { position: 3, city: 'Salvador', value: '145 kWh/m²' },
        { position: 4, city: 'Porto Alegre', value: '134 kWh/m²' },
        { position: 5, city: 'Curitiba', value: '115 kWh/m²' }
    ];

    const months = [
        { value: 'janeiro', label: 'Janeiro' },
        { value: 'fevereiro', label: 'Fevereiro' },
        { value: 'marco', label: 'Março' },
        { value: 'abril', label: 'Abril' },
        { value: 'maio', label: 'Maio' },
        { value: 'junho', label: 'Junho' },
        { value: 'julho', label: 'Julho' },
        { value: 'agosto', label: 'Agosto' },
        { value: 'setembro', label: 'Setembro' },
        { value: 'outubro', label: 'Outubro' },
        { value: 'novembro', label: 'Novembro' },
        { value: 'dezembro', label: 'Dezembro' }
    ];

    return (
        <Container maxWidth="xl" sx={{ px: 4 }}>
            {/* Seletor de Mês */}
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
                <FormControl sx={{ minWidth: 200 }}>
                    <InputLabel>Selecione o mês</InputLabel>
                    <Select
                        value={selectedMonth}
                        onChange={(e) => onMonthChange?.(e.target.value)}
                        label="Selecione o mês"
                    >
                        {months.map((month) => (
                            <MenuItem key={month.value} value={month.value}>
                                {month.label}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </Box>

            {/* Gráficos de Energia */}
            <Box sx={{ 
                display: 'flex', 
                gap: 1.5, 
                mb: 4, 
                width: '100%',
                alignItems: 'stretch',
                overflow: 'hidden'
            }}>
                {/* Gráfico Energia Solar */}
                <Box sx={{ flex: '3', minWidth: '0' }}>
                    <Paper sx={{ 
                        p: 2.5, 
                        height: '450px',
                        boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
                        borderRadius: 2,
                        border: '1px solid #f0f0f0'
                    }}>
                        <Typography variant="h6" sx={{ 
                            mb: 2, 
                            color: '#333', 
                            fontWeight: 'bold',
                            fontSize: '16px',
                            lineHeight: 1.3
                        }}>
                            Estimativa mensal Geração de energia solar
                        </Typography>
                        <Box sx={{ height: 380 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart 
                                    data={solarData} 
                                    margin={{ top: 10, right: 15, left: 15, bottom: 40 }}
                                >
                                    <XAxis 
                                        dataKey="shortName" 
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fontSize: 10, fill: '#666' }}
                                        angle={-45}
                                        textAnchor="end"
                                        height={50}
                                        interval={0}
                                    />
                                    <YAxis 
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fontSize: 10, fill: '#666' }}
                                        width={35}
                                    />
                                    <Tooltip 
                                        formatter={(value: number) => [`${value} kWh/m²`]}
                                        labelFormatter={(label) => {
                                            const cityData = solarData.find(item => item.shortName === label);
                                            return cityData ? cityData.city : label;
                                        }}
                                        contentStyle={{
                                            backgroundColor: 'white',
                                            border: '1px solid #e0e0e0',
                                            borderRadius: '8px',
                                            color: '#333',
                                            fontSize: '12px',
                                            padding: '8px 12px',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                                        }}
                                    />
                                    <Bar 
                                        dataKey="value" 
                                        radius={[6, 6, 0, 0]}
                                    >
                                        {solarData.map((_, index) => (
                                            <Cell key={`cell-${index}`} fill="#FF9800" />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </Box>
                    </Paper>
                </Box>

                {/* Ranking Energia Solar */}
                <Box sx={{ flex: '2', minWidth: '0' }}>
                    <Paper sx={{ 
                        p: 3, 
                        height: '450px',
                        boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
                        borderRadius: 2,
                        border: '1px solid #f0f0f0'
                    }}>
                        <Typography variant="subtitle1" sx={{ 
                            mb: 2.5, 
                            fontWeight: 'bold', 
                            fontSize: '15px', 
                            textAlign: 'center',
                            lineHeight: 1.4,
                            color: '#333'
                        }}>
                            Cidades com maior<br />potencial para produção de<br />
                            <span style={{ color: '#FF9800', fontWeight: 'bold' }}>energia solar</span>
                        </Typography>
                        <div className={styles.rankingContainer}>
                            {solarRanking.map((item) => (
                                <div key={item.position} className={`${styles.rankingItem} ${styles.solarRankingItem}`}>
                                    <Chip 
                                        label={item.position + 'º'} 
                                        size="small" 
                                        className={`${styles.rankingChip} ${styles.solarChip}`}
                                    />
                                    <div className={styles.rankingCityName}>
                                        {item.city}
                                    </div>
                                    <div className={`${styles.rankingValue} ${styles.solarValue}`}>
                                        {item.value}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </Paper>
                </Box>

                {/* Gráfico Energia Eólica */}
                <Box sx={{ flex: '3', minWidth: '0' }}>
                    <Paper sx={{ 
                        p: 2.5, 
                        height: '450px',
                        boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
                        borderRadius: 2,
                        border: '1px solid #f0f0f0'
                    }}>
                        <Typography variant="h6" sx={{ 
                            mb: 2, 
                            color: '#333', 
                            fontWeight: 'bold',
                            fontSize: '16px',
                            lineHeight: 1.3
                        }}>
                            Estimativa mensal Geração de energia eólica
                        </Typography>
                        <Box sx={{ height: 380 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart 
                                    data={windData} 
                                    margin={{ top: 10, right: 15, left: 15, bottom: 40 }}
                                >
                                    <XAxis 
                                        dataKey="shortName" 
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fontSize: 10, fill: '#666' }}
                                        angle={-45}
                                        textAnchor="end"
                                        height={50}
                                        interval={0}
                                    />
                                    <YAxis 
                                        axisLine={false}
                                        tickLine={false}
                                        tick={{ fontSize: 10, fill: '#666' }}
                                        width={35}
                                    />
                                    <Tooltip 
                                        formatter={(value: number) => [`${value} kWh/m²`]}
                                        labelFormatter={(label) => {
                                            const cityData = windData.find(item => item.shortName === label);
                                            return cityData ? cityData.city : label;
                                        }}
                                        contentStyle={{
                                            backgroundColor: 'white',
                                            border: '1px solid #e0e0e0',
                                            borderRadius: '8px',
                                            color: '#333',
                                            fontSize: '12px',
                                            padding: '8px 12px',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                                        }}
                                    />
                                    <Bar 
                                        dataKey="value" 
                                        radius={[6, 6, 0, 0]}
                                    >
                                        {windData.map((_, index) => (
                                            <Cell key={`cell-${index}`} fill="#2196F3" />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </Box>
                    </Paper>
                </Box>

                {/* Ranking Energia Eólica */}
                <Box sx={{ flex: '2', minWidth: '0' }}>
                    <Paper sx={{ 
                        p: 3, 
                        height: '450px',
                        boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
                        borderRadius: 2,
                        border: '1px solid #f0f0f0'
                    }}>
                        <Typography variant="subtitle1" sx={{ 
                            mb: 2.5, 
                            fontWeight: 'bold', 
                            fontSize: '15px', 
                            textAlign: 'center',
                            lineHeight: 1.4,
                            color: '#333'
                        }}>
                            Cidades com maior<br />potencial para produção de<br />
                            <span style={{ color: '#2196F3', fontWeight: 'bold' }}>energia eólica</span>
                        </Typography>
                        <div className={styles.rankingContainer}>
                            {windRanking.map((item) => (
                                <div key={item.position} className={`${styles.rankingItem} ${styles.windRankingItem}`}>
                                    <Chip 
                                        label={item.position + 'º'} 
                                        size="small" 
                                        className={`${styles.rankingChip} ${styles.windChip}`}
                                    />
                                    <div className={styles.rankingCityName}>
                                        {item.city}
                                    </div>
                                    <div className={`${styles.rankingValue} ${styles.windValue}`}>
                                        {item.value}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </Paper>
                </Box>
            </Box>
        </Container>
    );
};

export default EnergyCharts;
