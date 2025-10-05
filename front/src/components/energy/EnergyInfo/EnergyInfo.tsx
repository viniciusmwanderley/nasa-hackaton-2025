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

interface EnergyInfoProps {
    selectedCity?: string;
    onCityChange?: (city: string) => void;
}

const EnergyInfo: React.FC<EnergyInfoProps> = ({ 
    selectedCity = 'fortaleza', 
    onCityChange 
}) => {
    // Dados dos indicadores locais
    const localIndicators = [
        {
            title: 'Temperatura média anual',
            value: '27°',
            color: '#FF5722',
            source: 'NASA'
        },
        {
            title: 'Precipitação média anual',
            value: '1,608',
            color: '#2196F3',
            source: 'NASA'
        },
        {
            title: 'Velocidade média do vento',
            value: '7.5',
            color: '#4CAF50',
            source: 'NASA'
        },
        {
            title: 'Irradiação solar média',
            value: '5.8',
            color: '#FF9800',
            source: 'NASA'
        }
    ];

    const cities = [
        { value: 'fortaleza', label: 'Fortaleza' },
        { value: 'salvador', label: 'Salvador' },
        { value: 'recife', label: 'Recife' },
        { value: 'brasilia', label: 'Brasília' },
        { value: 'belo-horizonte', label: 'Belo Horizonte' },
        { value: 'sao-paulo', label: 'São Paulo' },
        { value: 'rio-janeiro', label: 'Rio de Janeiro' },
        { value: 'curitiba', label: 'Curitiba' },
        { value: 'porto-alegre', label: 'Porto Alegre' },
        { value: 'manaus', label: 'Manaus' },
        { value: 'belem', label: 'Belém' },
        { value: 'goiania', label: 'Goiânia' },
        { value: 'florianopolis', label: 'Florianópolis' },
        { value: 'vitoria', label: 'Vitória' },
        { value: 'maceio', label: 'Maceió' },
        { value: 'joao-pessoa', label: 'João Pessoa' },
        { value: 'natal', label: 'Natal' },
        { value: 'teresina', label: 'Teresina' },
        { value: 'sao-luis', label: 'São Luís' },
        { value: 'campo-grande', label: 'Campo Grande' },
        { value: 'cuiaba', label: 'Cuiabá' },
        { value: 'porto-velho', label: 'Porto Velho' },
        { value: 'rio-branco', label: 'Rio Branco' },
        { value: 'boa-vista', label: 'Boa Vista' },
        { value: 'macapa', label: 'Macapá' },
        { value: 'palmas', label: 'Palmas' },
        { value: 'aracaju', label: 'Aracaju' },
        { value: 'santa-luzia', label: 'Santa Luzia' },
        { value: 'patos', label: 'Patos' }
    ];

    return (
        <Container maxWidth="xl" sx={{ px: 4 }}>
            {/* Seletor de Cidade */}
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
                <FormControl sx={{ minWidth: 200 }}>
                    <InputLabel>Cidade</InputLabel>
                    <Select
                        value={selectedCity}
                        onChange={(e) => onCityChange?.(e.target.value)}
                        label="Cidade"
                    >
                        {cities.map((city) => (
                            <MenuItem key={city.value} value={city.value}>
                                {city.label}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            </Box>

            {/* Indicadores Locais */}
            <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', mb: 3 }}>
                {localIndicators.map((indicator, index) => (
                    <Box key={index} sx={{ flex: '1 1 250px', minWidth: '250px' }}>
                        <Card sx={{ 
                            height: 140,
                            background: `linear-gradient(135deg, ${indicator.color}20, ${indicator.color}40)`,
                            position: 'relative',
                            overflow: 'hidden'
                        }}>
                            <CardContent sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
                                <Box sx={{ 
                                    backgroundColor: '#7B4CBF', 
                                    color: 'white', 
                                    px: 1, 
                                    py: 0.5, 
                                    borderRadius: 1,
                                    fontSize: '10px',
                                    fontWeight: 'bold',
                                    alignSelf: 'flex-start',
                                    mb: 1
                                }}>
                                    Origem dos dados<br />
                                    {indicator.source}
                                </Box>
                                
                                <Typography variant="h6" sx={{ 
                                    fontWeight: 'bold', 
                                    color: '#333',
                                    fontSize: '14px',
                                    mb: 1,
                                    lineHeight: 1.2
                                }}>
                                    {indicator.title}
                                </Typography>
                                
                                <Typography variant="h3" sx={{ 
                                    fontWeight: 'bold', 
                                    color: indicator.color,
                                    fontSize: '48px',
                                    lineHeight: 1,
                                    mt: 'auto'
                                }}>
                                    {indicator.value}
                                </Typography>
                            </CardContent>
                        </Card>
                    </Box>
                ))}
            </Box>

            {/* Cards de Informação */}
            <Box sx={{ display: 'flex', gap: 3, mt: 2, flexWrap: 'wrap' }}>
                <Box sx={{ flex: '1 1 45%', minWidth: '300px' }}>
                    <Card sx={{ backgroundColor: '#FFF3C4', p: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                            Potencial Solar, (kWh/m²). Oque esse indicador significa?
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#666' }}>
                            (kWh/m²), este valor representa a quantidade total de energia solar 
                            que um metro quadrado de um painel fotovoltaico de alta eficiência 
                            geraria naquele local. Em termos simples, é uma medida direta de "o 
                            quão ensolarado" é produtivo para energia solar um lugar é. Quanto 
                            maior o número, mais eletricidade um painel pode gerar.
                        </Typography>
                    </Card>
                </Box>
                <Box sx={{ flex: '1 1 45%', minWidth: '300px' }}>
                    <Card sx={{ backgroundColor: '#E3F2FD', p: 2 }}>
                        <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                            Potencial Eólico, (kWh/m²). Oque esse indicador significa?
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#666' }}>
                            Este valor representa a quantidade de energia cinética do vento que 
                            um metro quadrado da área varrida pelas pás de uma turbina eólica 
                            moderna comercial em eletricidade. É uma medida direta da força e 
                            constância dos ventos ideais para a geração de energia. Lugares com valores 
                            altos possuem ventos ideais para parques eólicos.
                        </Typography>
                    </Card>
                </Box>
            </Box>
        </Container>
    );
};

export default EnergyInfo;
