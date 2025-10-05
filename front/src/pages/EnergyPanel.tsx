import React, { useState } from 'react';
import { Box } from '@mui/material';
import { EnergyHeader, EnergyCharts, EnergyInfo } from '../components/energy';
import { fetchMultipleEnergyData } from '../utils/api';
import type { Location } from '../types/app';
import type { ProcessedCityEnergyData } from '../types/api';

interface EnergyPanelProps {
    onBackToDashboard?: () => void;
}

const EnergyPanel: React.FC<EnergyPanelProps> = ({ onBackToDashboard }) => {
    const [selectedMonth, setSelectedMonth] = useState('01');
    const [selectedCityIndex, setSelectedCityIndex] = useState('0');
    const [selectedLocations, setSelectedLocations] = useState<Location[]>([]);
    const [energyData, setEnergyData] = useState<ProcessedCityEnergyData[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    const resetCitySelection = () => {
        setSelectedCityIndex('0');
    };

    const loadMultipleLocationsData = async (locations: Location[]) => {
        if (locations.length === 0) {
            setEnergyData([]);
            return;
        }

        setIsAnalyzing(true);
        setError(null);

        try {
            const locationsWithNames = locations.map(loc => ({
                latitude: loc.latitude,
                longitude: loc.longitude,
                cityName: `${loc.city}, ${loc.state}`
            }));

            const data = await fetchMultipleEnergyData(locationsWithNames);
            setEnergyData(data);
            resetCitySelection(); 
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Erro ao carregar dados das cidades');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleLocationsChange = (locations: Location[]) => {
        setSelectedLocations(locations);
    };

    const handleMonthChange = (month: string) => {
        setSelectedMonth(month);
    };

    const handleCityChange = (cityIndex: string) => {
        setSelectedCityIndex(cityIndex);
    };

    return (
        <Box sx={{ backgroundColor: '#f5f7fa', minHeight: '100vh' }}>
            <EnergyHeader 
                onLocationsChange={handleLocationsChange}
                selectedMonth={selectedMonth}
                onMonthChange={handleMonthChange}
                onAnalyzeClick={loadMultipleLocationsData}
                isAnalyzing={isAnalyzing}
                onBackToDashboard={onBackToDashboard}
            />
            
            <EnergyCharts 
                selectedMonth={selectedMonth} 
                onMonthChange={handleMonthChange}
                energyData={energyData}
                loading={isAnalyzing}
                error={error}
            />
            
            <EnergyInfo 
                selectedCity={selectedCityIndex} 
                onCityChange={handleCityChange}
                error={error}
                availableCities={energyData}
            />
        </Box>
    );
};

export default EnergyPanel;