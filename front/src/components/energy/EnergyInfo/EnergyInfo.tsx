import React from 'react';
import {
    Box,
    Typography,
    Card,
    CardContent,
    Container,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Alert
} from '@mui/material';
import styles from './EnergyInfo.module.css';
import type { ProcessedCityEnergyData } from '../../../types/api';

interface EnergyInfoProps {
    selectedCity?: string;
    onCityChange?: (city: string) => void;
    error?: string | null;
    availableCities?: ProcessedCityEnergyData[];
}

const EnergyInfo: React.FC<EnergyInfoProps> = ({ 
    selectedCity = '', 
    onCityChange,
    error = null,
    availableCities = []
}) => {
    // Obtém dados da cidade selecionada
    const getCurrentCityData = () => {
        if (!selectedCity || !availableCities.length) return null;
        const cityIndex = parseInt(selectedCity, 10);
        return availableCities[cityIndex] || null;
    };

    const currentCityData = getCurrentCityData();

    // Função para obter dados dos indicadores a partir da API
    const getLocalIndicators = () => {
        if (!currentCityData) {
            // Dados de fallback quando não há dados da API
            return [
                {
                    title: 'Angle for Maximum Irradiation',
                    value: '--',
                    unit: '°',
                    backgroundColor: '#F9DA5F',
                    backgroundImage: '/ClimateIndicatorVectorY.png',
                    textColor: 'black',
                    group: 'solar'
                },
                {
                    title: ' Solar Irradiance Index',
                    value: '--',
                    unit: 'kWh/m²/day',
                    backgroundColor: '#C75906',
                    backgroundImage: '/ClimateIndicatorVectorO.png',
                    textColor: 'white',
                    group: 'solar'
                },
                {
                    title: 'Air Density',
                    value: '--',
                    unit: 'kg/m³',
                    backgroundColor: '#BACCE3',
                    backgroundImage: '/ClimateIndicatorVectorLB.png',
                    textColor: 'black',
                    group: 'wind'
                },
                {
                    title: 'Wind Speed at 50m',
                    value: '--',
                    unit: 'm/s',
                    backgroundColor: '#0B357E',
                    backgroundImage: '/ClimateIndicatorVectorB.png',
                    textColor: 'white',
                    group: 'wind'
                }
            ];
        }

        return [
            {
                title: 'Angle for Maximum Irradiation',
                value: currentCityData.indicators.optimalAngle.toFixed(1),
                unit: '°',
                backgroundColor: '#F9DA5F',
                backgroundImage: '/ClimateIndicatorVectorY.png',
                textColor: 'black',
                group: 'solar'
            },
            {
                title: ' Solar Irradiance Index',
                value: currentCityData.indicators.solarIrradiance.toFixed(2),
                unit: 'kWh/m²/day',
                backgroundColor: '#C75906',
                backgroundImage: '/ClimateIndicatorVectorO.png',
                textColor: 'white',
                group: 'solar'
            },
            {
                title: 'Air Density',
                value: currentCityData.indicators.airDensity.toFixed(2),
                unit: 'kg/m³',
                backgroundColor: '#BACCE3',
                backgroundImage: '/ClimateIndicatorVectorLB.png',
                textColor: 'black',
                group: 'wind'
            },
            {
                title: 'Wind Speed at 50m',
                value: currentCityData.indicators.windSpeed.toFixed(1),
                unit: 'm/s',
                backgroundColor: '#0B357E',
                backgroundImage: '/ClimateIndicatorVectorB.png',
                textColor: 'white',
                group: 'wind'
            }
        ];
    };

    const localIndicators = getLocalIndicators();

    // Separa os indicadores por grupo para o novo layout
    const solarIndicators = localIndicators.filter(ind => ind.group === 'solar');
    const windIndicators = localIndicators.filter(ind => ind.group === 'wind');
    
    // Gera lista de cidades disponíveis a partir dos dados carregados
    const cities = availableCities.map((city, index) => ({
        value: index.toString(),
        label: city.cityName,
        data: city
    }));

    const renderIndicatorCard = (indicator: typeof localIndicators[number], index: number) => (
        <Card key={index} className={styles.indicatorCard} sx={{
            backgroundColor: indicator.backgroundColor,
        }}>
            <CardContent className={styles.cardContent}>
                <Typography 
                    className={styles.indicatorTitle}
                    sx={{ color: indicator.textColor }}
                >
                    {indicator.title}
                </Typography>
                
                <Box className={styles.valueContainer}>
                    <Typography 
                        className={styles.indicatorValue}
                        sx={{ color: indicator.textColor }}
                    >
                        {indicator.value}
                    </Typography>
                    <Typography 
                        className={styles.indicatorUnit}
                        sx={{ color: indicator.textColor }}
                    >
                        {indicator.unit}
                    </Typography>
                </Box>
            </CardContent>
            <Box 
                className={styles.cardBackgroundVector}
                sx={{ backgroundImage: `url(${indicator.backgroundImage})` }}
            />
        </Card>
    );

    return (
        <Container maxWidth="xl" className={styles.container}>
            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}
            <Box className={styles.mainLayout}>
                {/* Seção Esquerda (Indicadores) */}
                <Box className={styles.leftSection}>
                    <Box className={styles.headerTab}>
                        <Typography variant="h5" className={styles.title}>
                             Local Generation Indicators
                        </Typography>
                        <FormControl variant="outlined" className={styles.citySelector}>
                            <InputLabel 
                                shrink 
                                className={styles.citySelectorLabel}
                            >
                                Select a City
                            </InputLabel>
                            <Select
                                value={selectedCity}
                                onChange={(e) => onCityChange?.(e.target.value)}
                                label="Select a City"
                                disabled={cities.length === 0}
                                className={styles.citySelect}
                                displayEmpty
                                renderValue={(value) => {
                                    if (!value && cities.length === 0) {
                                        return (
                                            <Typography className={styles.waitingText}>
                                                Waiting For Cities
                                            </Typography>
                                        );
                                    }
                                    if (!value) {
                                        return 'Select a city';
                                    }
                                    const selectedCity = cities.find(city => city.value === value);
                                    return selectedCity ? selectedCity.label : 'Select a city';
                                }}
                                MenuProps={{
                                    PaperProps: {
                                        className: styles.cityDropdownPaper
                                    }
                                }}
                            >
                                {cities.length > 0 ? (
                                    cities.map((city) => (
                                        <MenuItem 
                                            key={city.value} 
                                            value={city.value}
                                            className={styles.cityMenuItem}
                                        >
                                            {city.label}
                                        </MenuItem>
                                    ))
                                ) : (
                                    <MenuItem value="" disabled className={styles.waitingMenuItem}>
                                        <Typography className={styles.waitingMessage}>
                                            Generate analysis for cities in the panel above
                                        </Typography>
                                    </MenuItem>
                                )}
                            </Select>
                        </FormControl>
                    </Box>

                    {/* Container principal para os grupos de indicadores */}
                    <Box className={styles.indicatorsRowContainer}>
                        {/* Grupo Solar */}
                        <Box className={styles.indicatorGroup}>
                            <Box className={styles.nasaLabel}>
                                <Typography className={styles.nasaLabelText}>
                                    Data Source<br/><b>NASA POWER</b>
                                </Typography>
                            </Box>
                            <Box className={styles.cardsRow}>
                                {solarIndicators.map(renderIndicatorCard)}
                            </Box>
                        </Box>
                        
                        {/* Grupo Eólico */}
                        <Box className={styles.indicatorGroup}>
                            <Box className={styles.nasaLabel}>
                                <Typography className={styles.nasaLabelText}>
                                    Data Source<br/><b>NASA POWER</b>
                                </Typography>
                            </Box>
                            <Box className={styles.cardsRow}>
                                {windIndicators.map(renderIndicatorCard)}
                            </Box>
                        </Box>
                    </Box>
                </Box>

                {/* Seção Direita (Informações) */}
                <Box className={styles.rightSection}>
                    <Card className={`${styles.infoCard} ${styles.solarInfoCard}`}>
                        <CardContent>
                            <Typography variant="h6" className={styles.infoCardTitle}>
                                Solar Potential, (kWh/m²). What this indicator means?
                            </Typography>
                            <Typography variant="body2" className={styles.infoCardDescription}>
                                (kWh/m²), this value represents the total amount of solar energy
                                that one square meter of a high-efficiency photovoltaic panel
                                would generate at that location. In simple terms, it is a direct measure of "how sunny"
                                and productive a place is for solar energy. The higher the number, the more electricity
                                a panel can generate.
                            </Typography>
                        </CardContent>
                    </Card>
                    
                    <Card className={`${styles.infoCard} ${styles.windInfoCard}`}>
                        <CardContent>
                            <Typography variant="h6" className={styles.infoCardTitle}>
                                Wind Potential, (kWh/m²). What this indicator means?
                            </Typography>
                            <Typography variant="body2" className={styles.infoCardDescription}>
                                This value represents the amount of kinetic energy in the wind that
                                one square meter of the area swept by the blades of a modern wind turbine
                                would convert into electricity. It is a direct measure of the strength and
                                constancy of the winds for energy generation. Places with high values
                                have ideal winds for wind farms.
                            </Typography>
                        </CardContent>
                    </Card>
                </Box>
            </Box>
        </Container>
    );
};

export default EnergyInfo;