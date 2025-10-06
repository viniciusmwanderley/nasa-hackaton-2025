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
    Button
} from '@mui/material';
import { Search, Close, ArrowDropDown, Send, ArrowBack } from '@mui/icons-material';
import styles from './EnergyHeader.module.css';
import { geocodeLocation } from '../../../utils/api';
import type { Location } from '../../../types/app';

interface EnergyHeaderProps {
    onLocationsChange?: (locations: Location[]) => void;
    selectedMonth?: string;
    onMonthChange?: (month: string) => void;
    onAnalyzeClick?: (locations: Location[], month: string) => void;
    isAnalyzing?: boolean;
    onBackToDashboard?: () => void;
}

const EnergyHeader: React.FC<EnergyHeaderProps> = ({ 
    onLocationsChange,
    selectedMonth = '',
    onMonthChange,
    onAnalyzeClick,
    isAnalyzing = false,
    onBackToDashboard
}) => {
    const [locationQuery, setLocationQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState<Location[]>([]);
    const [selectedLocations, setSelectedLocations] = useState<Location[]>([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [showSelectedCities, setShowSelectedCities] = useState(false); 

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
            
            const filteredResults = locations.filter(location => 
                !selectedLocations.some(selected => 
                    selected.city.toLowerCase() === location.city.toLowerCase() &&
                    selected.state.toLowerCase() === location.state.toLowerCase()
                )
            );
            
            setSearchResults(filteredResults);
        } catch (error) {
            console.error('Error searching for locations:', error);
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
            setShowSelectedCities(true);
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
            setShowSelectedCities(false);
        }
    };

    const handleClearAllLocations = () => {
        setSelectedLocations([]);
        onLocationsChange?.([]);
        setShowDropdown(false);
        setShowSelectedCities(false);
        setLocationQuery('');
        setSearchResults([]);
    }

    const handleClickAway = () => {
        setShowDropdown(false);
        setShowSelectedCities(false);
        setSearchResults([]);
    };

    const handleInputClick = () => {
        if (selectedLocations.length > 0) {
            setShowSelectedCities(!showSelectedCities);
        }
        if (selectedLocations.length < 5) {
            setShowDropdown(true);
        }
    };

    const isGenerateEnabled = selectedLocations.length >= 1 && selectedLocations.length <= 5 && !isAnalyzing;

    return (
        <div className={styles.container}>
            <div className={styles.topHeader}>
                <div className={styles.logoSection}>
                    <Button
                        startIcon={<ArrowBack />}
                        onClick={onBackToDashboard}
                        className={styles.backButton}
                    >
                        Back to Dashboard
                    </Button>
                    <img 
                        src="/weatherdata.png" 
                        alt="CLIMADATA" 
                        className={styles.logoImage}
                    />
                </div>
                <div className={styles.loadingInfo}>
                    Loading may take up to 2 minutes as we compile the necessary information for you.
                </div>
            </div>

            <Paper className={styles.whiteCard} elevation={2}>
                <div className={styles.mainRow}>
                    <div className={styles.titleSection}>
                        <Typography variant="h4" className={styles.title}>
                            Renewable Opportunities Indicators
                        </Typography>
                        <Typography variant="body2" className={styles.subtitle}>
                            Select 1 to 5 locations to generate energy analysis
                        </Typography>
                    </div>
                    
                    <div className={styles.controlsSection}>
                        <div className={styles.controlsRow}>
                            <div className={styles.controlGroup}>
                                <Select
                                    value={selectedMonth}
                                    onChange={(e) => onMonthChange?.(e.target.value)}
                                    displayEmpty
                                    variant="outlined"
                                    size="small"
                                    className={styles.monthSelect}
                                    MenuProps={{
                                        PaperProps: {
                                            className: styles.dropdownPaper
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
                            
                            <div className={styles.controlGroup}>
                                <ClickAwayListener onClickAway={handleClickAway}>
                                    <div className={styles.citiesInputWrapper}>
                                        <TextField
                                            size="small"
                                            placeholder={selectedLocations.length === 5 
                                                ? "Maximum 5 locations reached" 
                                                : `Search locations (${selectedLocations.length}/5)`
                                            }
                                            value={locationQuery}
                                            onChange={(e) => handleLocationSearch(e.target.value)}
                                            onFocus={handleInputClick}
                                            onClick={handleInputClick}
                                            variant="outlined"
                                            className={styles.citiesInput}
                                            disabled={selectedLocations.length === 5}
                                            InputProps={{
                                                startAdornment: (
                                                    <InputAdornment position="start">
                                                        <Search className={styles.searchIcon} />
                                                    </InputAdornment>
                                                ),
                                                endAdornment: isSearching ? (
                                                    <InputAdornment position="end">
                                                        <CircularProgress size={16} />
                                                    </InputAdornment>
                                                ) : selectedLocations.length === 5 ? (
                                                    <InputAdornment position="end">
                                                        <Typography variant="caption" color="textSecondary">
                                                            Max
                                                        </Typography>
                                                    </InputAdornment>
                                                ) : selectedLocations.length > 0 ? (
                                                    <InputAdornment position="end">
                                                        <ArrowDropDown 
                                                            className={styles.dropdownIcon}
                                                            style={{ 
                                                                transform: showSelectedCities ? 'rotate(180deg)' : 'rotate(0deg)',
                                                                transition: 'transform 0.2s ease'
                                                            }}
                                                        />
                                                    </InputAdornment>
                                                ) : null
                                            }}
                                        />

                                        {selectedLocations.length > 0 && showSelectedCities && (
                                            <div className={styles.selectedCitiesContainer}>
                                                <div className={styles.chipsWrapper}>
                                                    {selectedLocations.map((location, index) => (
                                                        <Chip
                                                            key={`${location.city}-${location.state}-${index}`}
                                                            label={`${location.city}, ${location.state}`}
                                                            size="small"
                                                            onDelete={() => handleLocationRemove(location)}
                                                            className={styles.locationChip}
                                                            deleteIcon={<Close className={styles.deleteIcon} />}
                                                        />
                                                    ))}
                                                </div>
                                                {selectedLocations.length > 0 && (
                                                    <div className={styles.clearAllSection}>
                                                        <Button
                                                            size="small"
                                                            onClick={handleClearAllLocations}
                                                            className={styles.clearAllButton}
                                                        >
                                                            Clear all ({selectedLocations.length})
                                                        </Button>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                        
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
                            
                            <div className={styles.controlGroup}>
                                <Button
                                    variant="contained"
                                    onClick={() => onAnalyzeClick?.(selectedLocations, selectedMonth)}
                                    disabled={!isGenerateEnabled}
                                    className={styles.analyzeButton}
                                    startIcon={isAnalyzing ? <CircularProgress size={16} /> : <Send />}
                                >
                                    {isAnalyzing ? 'Generating...' : 'Generate'}
                                </Button>
                                {selectedLocations.length > 0 && (
                                    <Typography variant="caption" className={styles.locationsCount}>
                                        {selectedLocations.length} location(s) selected
                                    </Typography>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </Paper>
        </div>
    );
};

export default EnergyHeader;