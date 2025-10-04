import React, { useState } from 'react';
import './Header.css';
import { useApp } from '../../../contexts/AppContext';
import { geocodeLocation } from '../../../utils/api';

const Header: React.FC = () => {
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const { setLocation } = useApp();

    const handleSearchToggle = () => {
        setIsSearchOpen(!isSearchOpen);
        if (!isSearchOpen) {
            setSearchQuery('');
            setSearchResults([]);
        }
    };

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;
        
        setIsSearching(true);
        try {
            const results = await geocodeLocation(searchQuery);
            setSearchResults(results);
        } catch (error) {
            console.error('Erro na busca:', error);
            setSearchResults([]);
        } finally {
            setIsSearching(false);
        }
    };

    const handleLocationSelect = (location: any) => {
        setLocation(location);
        setIsSearchOpen(false);
        setSearchQuery('');
        setSearchResults([]);
    };

    const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
        if (event.key === 'Enter') {
            handleSearch();
        }
    };

    return (
        <div className="app-header">
            <div className="header-container">
                <div className="header-brand">
                    <div className="climadata-logo">
                        <img src="/climadata.png" alt="CLIMADATA" className="logo-image" />
                    </div>
                </div>
                
                <div className="header-actions">
                    <div className={`search-container ${isSearchOpen ? 'open' : ''}`}>
                        {isSearchOpen && (
                            <div className="search-input-container">
                                <input
                                    type="text"
                                    placeholder="Buscar localização..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    onKeyPress={handleKeyPress}
                                    className="search-input"
                                    autoFocus
                                />
                                {searchResults.length > 0 && (
                                    <div className="search-results">
                                        {searchResults.map((location, index) => (
                                            <div
                                                key={index}
                                                className="search-result-item"
                                                onClick={() => handleLocationSelect(location)}
                                            >
                                                <span className="location-icon">📍</span>
                                                <span className="location-name">
                                                    {location.city}, {location.state}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                {isSearching && (
                                    <div className="search-loading">Buscando...</div>
                                )}
                            </div>
                        )}
                    </div>
                    
                    <button 
                        className={`search-button ${isSearchOpen ? 'active' : ''}`} 
                        onClick={handleSearchToggle}
                    >
                        {isSearchOpen ? '✕' : '🔍'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Header;