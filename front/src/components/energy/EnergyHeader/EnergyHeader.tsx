import React, { useState, useCallback } from 'react';
import {
    Typography,
    Paper,
    TextField,
    InputAdornment,
    CircularProgress,
    Chip,
    ClickAwayListener,
    Select,
    MenuItem,
    IconButton
} from '@mui/material';
import { Search, Close, ArrowDropDown } from '@mui/icons-material';
import styles from './EnergyHeader.module.css';
import { geocodeLocation } from '../../../utils/api';
import type { Location } from '../../../types/app';

interface EnergyHeaderProps {
    onLocationsChange?: (locations: Location[]) => void;
}

const EnergyHeader: React.FC<EnergyHeaderProps> = ({ onLocationsChange }) => {
    const [locationQuery, setLocationQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState<Location[]>([]);
    const [selectedLocations, setSelectedLocations] = useState<Location[]>([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [selectedMonth, setSelectedMonth] = useState<string>(''); 

    const handleLocationSearch = useCallback(async (query: string) => {
        setLocationQuery(query);
        setShowDropdown(true);
        
        if (query.length < 2) {
            setSearchResults([]);
            return;
        }

        setIsSearching(true);
        
        try {
            const locations = await geocodeLocation(query);
            
            // Filtra locações que já foram selecionadas
            const filteredResults = locations.filter(location => 
                !selectedLocations.some(selected => 
                    selected.city.toLowerCase() === location.city.toLowerCase() &&
                    selected.state.toLowerCase() === location.state.toLowerCase()
                )
            );
            
            setSearchResults(filteredResults);
        } catch (error) {
            console.error('Erro ao buscar localização:', error);
            setSearchResults([]);
        } finally {
            setIsSearching(false);
        }
    }, [selectedLocations]);

    const handleLocationSelect = (location: Location) => {
        if (selectedLocations.length < 5 && !selectedLocations.some(selected => 
            selected.city === location.city && selected.state === location.state
        )) {
            const newLocations = [...selectedLocations, location];
            setSelectedLocations(newLocations);
            onLocationsChange?.(newLocations);
        }
        setLocationQuery('');
        setSearchResults([]);
        setShowDropdown(false);
    };

    const handleLocationRemove = (location: Location) => {
        const newLocations = selectedLocations.filter(loc => 
            !(loc.city === location.city && loc.state === location.state)
        );
        setSelectedLocations(newLocations);
        onLocationsChange?.(newLocations);
        if (newLocations.length === 0) {
            setShowDropdown(false);
        }
    };

    const handleClearAllLocations = () => {
        setSelectedLocations([]);
        onLocationsChange?.([]);
        setShowDropdown(false);
        setLocationQuery('');
        setSearchResults([]);
    }

    const handleClickAway = () => {
        if (selectedLocations.length < 5) {
            setShowDropdown(false);
        }
        setSearchResults([]);
    };

    // Renderização do componente
    return (
        <div>
            {/* Logo */}
            <div className={styles.logoSection}>
                <img 
                    src="/weatherdata.png" 
                    alt="CLIMADATA" 
                    className={styles.logoImage}
                />
            </div>

            {/* Card branco principal */}
            <div className={styles.whiteCard}>
                <div className={styles.mainRow}>
                    {/* Título */}
                    <div className={styles.titleSection}>
                        <Typography variant="h4" className={styles.title}>
                            Indicadores de Oportunidades Renováveis
                        </Typography>
                    </div>
                    
                    {/* Seleção de mês */}
                    <div className={styles.monthSection}>
                        <Select
                            value={selectedMonth}
                            onChange={(e) => setSelectedMonth(e.target.value)}
                            displayEmpty
                            variant="standard" // Adicionado
                            disableUnderline // Adicionado
                            IconComponent={ArrowDropDown} // Opcional: Garante o ícone de dropdown (seta)
                            MenuProps={{
                                PaperProps: {
                                    className: styles.monthDropdownPaper // Nova classe para o Paper
                                }
                            }}
                        >
                            <MenuItem value="">Select a month</MenuItem>
                            <MenuItem value="01">January</MenuItem>
                            <MenuItem value="02">February</MenuItem>
                            <MenuItem value="03">March</MenuItem>
                            <MenuItem value="04">April</MenuItem>
                            <MenuItem value="05">May</MenuItem>
                            <MenuItem value="06">June</MenuItem>
                            <MenuItem value="07">July</MenuItem>
                            <MenuItem value="08">August</MenuItem>
                            <MenuItem value="09">September</MenuItem>
                            <MenuItem value="10">October</MenuItem>
                            <MenuItem value="11">November</MenuItem>
                            <MenuItem value="12">December</MenuItem>
                        </Select>
                    </div>
                    
                    {/* Input de cidades expansível */}
                    <div className={styles.citiesSection}>
                        <ClickAwayListener onClickAway={handleClickAway}>
                            <div style={{ position: 'relative' }}>
                                
                                {/* Campo de busca fixo no card */}
                                <div 
                                    className={styles.searchField}
                                    onClick={() => setShowDropdown(true)}
                                >
                                    <TextField
                                        size="small"
                                        placeholder="Busque até 5 locais"
                                        value={locationQuery}
                                        onChange={(e) => handleLocationSearch(e.target.value)}
                                        onFocus={() => setShowDropdown(true)}
                                        variant="standard"
                                        InputProps={{
                                            disableUnderline: true,
                                            startAdornment: !locationQuery ? (
                                                <InputAdornment position="start">
                                                    <Search />
                                                </InputAdornment>
                                            ) : null,
                                            endAdornment: isSearching ? (
                                                <InputAdornment position="end">
                                                    <CircularProgress size={14} />
                                                </InputAdornment>
                                            ) : null
                                        }}
                                    />
                                </div>

                                {/* Container das cidades selecionadas - aparece abaixo e fora do card */}
                                {selectedLocations.length > 0 && (
                                    <div className={styles.selectedCitiesContainer}>
                                        {/* Chips das cidades selecionadas */}
                                        {selectedLocations.map((location, index) => (
                                            <div
                                                key={`${location.city}-${location.state}-${index}`}
                                                className={styles.cityChipContainer}
                                            >
                                                <Chip
                                                    label={`${location.city}, ${location.state}`}
                                                    size="small"
                                                    onDelete={() => handleLocationRemove(location)}
                                                />
                                            </div>
                                        ))}

                                        {/* Botão para limpar todas as cidades quando há 5 */}
                                        {selectedLocations.length === 5 && (
                                            <div className={styles.clearAllButton}>
                                                <IconButton 
                                                    size="small" 
                                                    onClick={handleClearAllLocations}
                                                >
                                                    <Close fontSize="small" />
                                                </IconButton>
                                            </div>
                                        )}
                                    </div>
                                )}
                                
                                {/* Dropdown de resultados da API */}
                                {showDropdown && searchResults.length > 0 && selectedLocations.length < 5 && (
                                    <Paper className={styles.dropdown}>
                                        {searchResults.map((location, index) => (
                                            <div
                                                key={index}
                                                className={styles.dropdownItem}
                                                onClick={() => handleLocationSelect(location)}
                                            >
                                                <Typography variant="body2">
                                                    {`${location.city}, ${location.state}`}
                                                </Typography>
                                            </div>
                                        ))}
                                    </Paper>
                                )}
                            </div>
                        </ClickAwayListener>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default EnergyHeader;