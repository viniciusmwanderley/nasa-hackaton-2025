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
    InputLabel
} from '@mui/material';
import styles from './EnergyInfo.module.css';
import ClimateIndicatorVectorY from '../../../assets/ClimateIndicatorVectorY.png';
import ClimateIndicatorVectorO from '../../../assets/ClimateIndicatorVectorO.png';
import ClimateIndicatorVectorLB from '../../../assets/ClimateIndicatorVectorLB.png';
import ClimateIndicatorVectorB from '../../../assets/ClimateIndicatorVectorB.png';

interface EnergyInfoProps {
    selectedCity?: string;
    onCityChange?: (city: string) => void;
}

const EnergyInfo: React.FC<EnergyInfoProps> = ({ 
    selectedCity = 'fortaleza', 
    onCityChange 
}) => {
    // Dados dos indicadores locais conforme o design
    const localIndicators = [
        {
            title: 'Ângulo para irradiação máxima',
            value: '125',
            unit: '°',
            backgroundColor: '#F9DA5F',
            backgroundImage: ClimateIndicatorVectorY,
            textColor: 'black',
            group: 'solar'
        },
        {
            title: 'Índice de Irradiação Solar',
            value: '47',
            unit: 'kWh/m²',
            backgroundColor: '#C75906',
            backgroundImage: ClimateIndicatorVectorO,
            textColor: 'white',
            group: 'solar'
        },
        {
            title: 'Densidade do ar',
            value: '125',
            unit: 'Kg/m³',
            backgroundColor: '#BACCE3',
            backgroundImage: ClimateIndicatorVectorLB,
            textColor: 'black',
            group: 'wind'
        },
        {
            title: 'Velocidade do Vento a 50m',
            value: '47',
            unit: 'm/s',
            backgroundColor: '#0B357E',
            backgroundImage: ClimateIndicatorVectorB,
            textColor: 'white',
            group: 'wind'
        }
    ];

    // Separa os indicadores por grupo para o novo layout
    const solarIndicators = localIndicators.filter(ind => ind.group === 'solar');
    const windIndicators = localIndicators.filter(ind => ind.group === 'wind');
    
    const cities = [
        { value: 'fortaleza', label: 'Fortaleza' },
        { value: 'salvador', label: 'Salvador' },
        { value: 'recife', label: 'Recife' }
    ];

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
            <Box className={styles.mainLayout}>
                {/* Seção Esquerda (Indicadores) */}
                <Box className={styles.leftSection}>
                    <Box className={styles.headerTab}>
                        <Typography variant="h5" className={styles.title}>
                            Indicadores Locais de Geração
                        </Typography>
                        <FormControl variant="outlined" className={styles.citySelector}>
                            <InputLabel>Selecione uma Cidade</InputLabel>
                            <Select
                                value={selectedCity}
                                onChange={(e) => onCityChange?.(e.target.value)}
                                label="Selecione uma Cidade"
                            >
                                {cities.map((city) => (
                                    <MenuItem key={city.value} value={city.value}>
                                        {city.label}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Box>

                    {/* Container principal para os grupos de indicadores */}
                    <Box className={styles.indicatorsRowContainer}>
                        {/* Grupo Solar */}
                        <Box className={styles.indicatorGroup}>
                            <Box className={styles.nasaLabel}>
                                <Typography className={styles.nasaLabelText}>
                                    Origem dos dados<br/><b>NASA POWER</b>
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
                                    Origem dos dados<br/><b>NASA POWER</b>
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
                                Potencial Solar, (kWh/m²). Oque esse indicador significa?
                            </Typography>
                            <Typography variant="body2" className={styles.infoCardDescription}>
                                (kWh/m²), este valor representa a quantidade total de energia solar 
                                que um metro quadrado de um painel fotovoltaico de alta eficiência 
                                geraria naquele local. Em termos simples, é uma medida direta de "o 
                                quão ensolarado" e produtivo para energia solar um lugar é. Quanto 
                                maior o número, mais eletricidade um painel pode gerar.
                            </Typography>
                        </CardContent>
                    </Card>
                    
                    <Card className={`${styles.infoCard} ${styles.windInfoCard}`}>
                        <CardContent>
                            <Typography variant="h6" className={styles.infoCardTitle}>
                                Potencial Eólico, (kWh/m²). Oque esse indicador significa?
                            </Typography>
                            <Typography variant="body2" className={styles.infoCardDescription}>
                                Este valor representa a quantidade de energia cinética do vento que 
                                um metro quadrado da área varrida pelas pás de uma turbina eólica 
                                moderna converteria em eletricidade. É uma medida direta da força e 
                                constância dos ventos para a geração de energia. Lugares com valores 
                                altos possuem ventos ideais para parques eólicos.
                            </Typography>
                        </CardContent>
                    </Card>
                </Box>
            </Box>
        </Container>
    );
};

export default EnergyInfo;