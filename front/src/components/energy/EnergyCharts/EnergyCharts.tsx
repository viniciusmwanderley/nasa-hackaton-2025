import React from 'react';
import {
    Box,
    Typography,
    Paper,
    Chip,
    Container,
    Alert
} from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import styles from './EnergyCharts.module.css';
import { ChartSkeleton, RankingSkeleton } from '../../common/ChartSkeleton';

import type { ProcessedCityEnergyData } from '../../../types/api';

interface EnergyChartsProps {
    selectedMonth?: string;
    onMonthChange?: (month: string) => void;
    energyData?: ProcessedCityEnergyData[];
    loading?: boolean;
    error?: string | null;
}

const EnergyCharts: React.FC<EnergyChartsProps> = ({ 
    energyData = [],
    loading = false,
    error = null,
    selectedMonth = '01'
}) => {
    const monthKeys = {
        '01': 'JAN', '02': 'FEB', '03': 'MAR', '04': 'APR',
        '05': 'MAY', '06': 'JUN', '07': 'JUL', '08': 'AUG',
        '09': 'SEP', '10': 'OCT', '11': 'NOV', '12': 'DEC',
        'ANN': 'ANN'
    } as const;

    const currentMonthKey = monthKeys[selectedMonth as keyof typeof monthKeys] || 'ANN';
    const isAnnual = currentMonthKey === 'ANN';

    const generateShortName = (cityName: string): string => {
        const parts = cityName.split(',')[0].trim();
        const words = parts.split(' ');
        if (words.length === 1) {
            return words[0].substring(0, 3).toUpperCase();
        } else {
            return words.map(word => word[0]).join('').toUpperCase().substring(0, 3);
        }
    };

    const solarData = energyData.length > 0 ? energyData.map(city => ({
        city: city.cityName,
        shortName: generateShortName(city.cityName),
        value: isAnnual ? 
            Math.round(city.solarAnnual) : 
            Math.round(city.solarMonthly[currentMonthKey])
    })) : [];

    const windData = energyData.length > 0 ? energyData.map(city => ({
        city: city.cityName,
        shortName: generateShortName(city.cityName),
        value: isAnnual ? 
            Math.round(city.windAnnual) : 
            Math.round(city.windMonthly[currentMonthKey])
    })) : [];

    const solarRanking = energyData.length > 0 ? 
        [...energyData]
            .sort((a, b) => {
                const valueA = isAnnual ? a.solarAnnual : a.solarMonthly[currentMonthKey];
                const valueB = isAnnual ? b.solarAnnual : b.solarMonthly[currentMonthKey];
                return valueB - valueA;
            })
            .slice(0, 5)
            .map((city, index) => ({
                position: index + 1,
                city: city.cityName,
                value: `${Math.round(isAnnual ? city.solarAnnual : city.solarMonthly[currentMonthKey])} kWh/m²`
            })) : [];

    const windRanking = energyData.length > 0 ? 
        [...energyData]
            .sort((a, b) => {
                const valueA = isAnnual ? a.windAnnual : a.windMonthly[currentMonthKey];
                const valueB = isAnnual ? b.windAnnual : b.windMonthly[currentMonthKey];
                return valueB - valueA;
            })
            .slice(0, 5)
            .map((city, index) => ({
                position: index + 1,
                city: city.cityName,
                value: `${Math.round(isAnnual ? city.windAnnual : city.windMonthly[currentMonthKey])} kWh/m²`
            })) : [];

    return (
        <Container maxWidth="xl" sx={{ px: 4 }}>
            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}
            
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
            </Box>

            <Box sx={{ 
                display: 'flex', 
                gap: 1.5, 
                mb: 4, 
                width: '100%',
                alignItems: 'stretch',
                overflow: 'hidden'
            }}>
                <Box sx={{ flex: '3', minWidth: '0' }}>
                    {loading ? (
                        <ChartSkeleton />
                    ) : (
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
                                Monthly Solar Potential Estimate
                            </Typography>
                            <Box sx={{ height: 380 }}>
                                {solarData.length > 0 ? (
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
                            ) : (
                                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                                    <Typography variant="body2" color="text.secondary">
                                        Select cities in the search field above to view the data
                                    </Typography>
                                </Box>
                                )}
                            </Box>
                        </Paper>
                    )}
                </Box>

                <Box sx={{ flex: '2', minWidth: '0' }}>
                    {loading ? (
                        <RankingSkeleton />
                    ) : (
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
                               Cities with the Highest <span style={{ color: '#FF9800', fontWeight: 'bold' }}>Solar Power</span> Potential
                            </Typography>
                            <div className={styles.rankingContainer}>
                                {solarRanking.length > 0 ? (
                                solarRanking.map((item) => (
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
                                ))
                            ) : (
                                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
                                    <Typography variant="body2" color="text.secondary" textAlign="center">
                                        Select cities to see the ranking
                                    </Typography>
                                </Box>
                                )}
                            </div>
                        </Paper>
                    )}
                </Box>

                <Box sx={{ flex: '3', minWidth: '0' }}>
                    {loading ? (
                        <ChartSkeleton />
                    ) : (
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
                                Monthly Wind Potential Estimate
                            </Typography>
                            <Box sx={{ height: 380 }}>
                                {windData.length > 0 ? (
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
                            ) : (
                                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                                    <Typography variant="body2" color="text.secondary">
                                        Select cities in the search field above to view the data
                                    </Typography>
                                </Box>
                                )}
                            </Box>
                        </Paper>
                    )}
                </Box>

                <Box sx={{ flex: '2', minWidth: '0' }}>
                    {loading ? (
                        <RankingSkeleton />
                    ) : (
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
                                Cities with the Highest <span style={{ color: '#2196F3', fontWeight: 'bold' }}>Wind Power Generation</span> Potential
                            </Typography>
                            <div className={styles.rankingContainer}>
                                {windRanking.length > 0 ? (
                                windRanking.map((item) => (
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
                                ))
                            ) : (
                                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '300px' }}>
                                    <Typography variant="body2" color="text.secondary" textAlign="center">
                                        Select cities to see the ranking
                                    </Typography>
                                </Box>
                                )}
                            </div>
                        </Paper>
                    )}
                </Box>
            </Box>
        </Container>
    );
};

export default EnergyCharts;
