import React, { useState } from 'react';
import { Box } from '@mui/material';
import { EnergyHeader, EnergyCharts, EnergyInfo } from '../components/energy';
import type { Location } from '../types/app';

const EnergyPanel: React.FC = () => {
    const [selectedMonth, setSelectedMonth] = useState('janeiro');
    const [selectedCity, setSelectedCity] = useState('fortaleza');

    const handleLocationsChange = (locations: Location[]) => {
        // Aqui você pode implementar lógica adicional quando as localizações mudarem
        console.log('Localizações selecionadas:', locations);
        // Agora você tem acesso a latitude, longitude, cidade, estado e país de cada localização
        locations.forEach(location => {
            console.log(`${location.city}, ${location.state} - Lat: ${location.latitude}, Lon: ${location.longitude}`);
        });
    };

    const handleMonthChange = (month: string) => {
        setSelectedMonth(month);
        // Aqui você pode implementar lógica para buscar dados do mês selecionado
        console.log('Mês selecionado:', month);
    };

    const handleCityChange = (city: string) => {
        setSelectedCity(city);
        // Aqui você pode implementar lógica para buscar dados da cidade selecionada
        console.log('Cidade selecionada:', city);
    };

    return (
        <Box sx={{ backgroundColor: '#f5f7fa', minHeight: '100vh' }}>
            {/* Componente 1: Header com logo e busca de localizações */}
            <EnergyHeader onLocationsChange={handleLocationsChange} />
            
            {/* Componente 2: Gráficos e Rankings */}
            <EnergyCharts 
                selectedMonth={selectedMonth} 
                onMonthChange={handleMonthChange} 
            />
            
            {/* Componente 3: Informações adicionais */}
            <EnergyInfo 
                selectedCity={selectedCity} 
                onCityChange={handleCityChange} 
            />
        </Box>
    );
};

export default EnergyPanel;
