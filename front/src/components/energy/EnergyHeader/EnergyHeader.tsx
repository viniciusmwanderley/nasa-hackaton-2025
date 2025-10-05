import React, { useState, useCallback } from 'react';
import {
    Box,
    Typography,
    Paper,
    AppBar,
    Toolbar,
    TextField,
    InputAdornment,
    CircularProgress,
    Chip
} from '@mui/material';
import { Search } from '@mui/icons-material';

interface EnergyHeaderProps {
    onLocationsChange?: (locations: string[]) => void;
}

const EnergyHeader: React.FC<EnergyHeaderProps> = ({ onLocationsChange }) => {
    const [locationQuery, setLocationQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState<string[]>([]);
    const [selectedLocations, setSelectedLocations] = useState<string[]>([]);

    const handleLocationSearch = useCallback(async (query: string) => {
        setLocationQuery(query);
        
        if (query.length < 2) {
            setSearchResults([]);
            return;
        }

        setIsSearching(true);
        
        // Mock search results - replace with actual API call
        const mockResults = [
            'São Paulo, SP, Brasil',
            'Rio de Janeiro, RJ, Brasil',
            'Belo Horizonte, MG, Brasil',
            'Salvador, BA, Brasil',
            'Fortaleza, CE, Brasil'
        ].filter(city => 
            city.toLowerCase().includes(query.toLowerCase())
        );
        
        setTimeout(() => {
            setSearchResults(mockResults);
            setIsSearching(false);
        }, 500);
    }, []);

    const handleLocationSelect = (location: string) => {
        if (selectedLocations.length < 5 && !selectedLocations.includes(location)) {
            const newLocations = [...selectedLocations, location];
            setSelectedLocations(newLocations);
            onLocationsChange?.(newLocations);
        }
        setLocationQuery('');
        setSearchResults([]);
    };

    const handleLocationRemove = (location: string) => {
        const newLocations = selectedLocations.filter(loc => loc !== location);
        setSelectedLocations(newLocations);
        onLocationsChange?.(newLocations);
    };

    return (
        <AppBar position="static" sx={{ backgroundColor: 'white', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
            <Toolbar sx={{ justifyContent: 'space-between', py: 1, px: 4 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <img 
                        src="/weatherdata.png" 
                        alt="CLIMADATA" 
                        style={{ height: '40px', width: 'auto' }}
                    />
                    <Typography sx={{ color: '#1976d2', fontWeight: 'bold', fontSize: '18px' }}>
                        CLIMADATA
                    </Typography>
                </Box>
                
                <Typography variant="h4" sx={{ 
                    color: '#333', 
                    fontWeight: 'bold',
                    textAlign: 'center',
                    flex: 1,
                    fontSize: '24px'
                }}>
                    Indicadores de Oportunidades Renováveis
                </Typography>
                
                <Box sx={{ position: 'relative', width: 280 }}>
                    <TextField
                        size="small"
                        placeholder="Busque até 5 locais"
                        value={locationQuery}
                        onChange={(e) => handleLocationSearch(e.target.value)}
                        sx={{ width: '100%' }}
                        InputProps={{
                            startAdornment: (
                                <InputAdornment position="start">
                                    <Search />
                                </InputAdornment>
                            ),
                            endAdornment: isSearching ? (
                                <InputAdornment position="end">
                                    <CircularProgress size={16} />
                                </InputAdornment>
                            ) : null
                        }}
                    />
                    
                    {/* Resultados da busca */}
                    {searchResults.length > 0 && (
                        <Paper sx={{ 
                            position: 'absolute',
                            top: '100%',
                            left: 0,
                            right: 0,
                            zIndex: 1000,
                            maxHeight: 200,
                            overflow: 'auto',
                            mt: 0.5
                        }}>
                            {searchResults.map((location, index) => (
                                <Box
                                    key={index}
                                    sx={{
                                        p: 1.5,
                                        cursor: 'pointer',
                                        '&:hover': { backgroundColor: '#f5f5f5' },
                                        borderBottom: index < searchResults.length - 1 ? '1px solid #eee' : 'none'
                                    }}
                                    onClick={() => handleLocationSelect(location)}
                                >
                                    <Typography variant="body2">{location}</Typography>
                                </Box>
                            ))}
                        </Paper>
                    )}
                    
                    {/* Locais selecionados */}
                    {selectedLocations.length > 0 && (
                        <Box sx={{ 
                            position: 'absolute',
                            top: '100%',
                            left: 0,
                            right: 0,
                            zIndex: 999,
                            mt: searchResults.length > 0 ? '200px' : '4px'
                        }}>
                            <Paper sx={{ p: 1 }}>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                    {selectedLocations.map((location) => (
                                        <Chip
                                            key={location}
                                            label={location}
                                            size="small"
                                            onDelete={() => handleLocationRemove(location)}
                                            color="primary"
                                            variant="outlined"
                                        />
                                    ))}
                                </Box>
                            </Paper>
                        </Box>
                    )}
                </Box>
            </Toolbar>
        </AppBar>
    );
};

export default EnergyHeader;
