import React from 'react';
import './FilterBar.css';

interface FilterBarProps {
    selectedMonth: string;
    onMonthChange: (month: string) => void;
    selectedUnit: string;
    onUnitChange: (unit: string) => void;
    selectedLocation: string;
    onLocationChange: (location: string) => void;
}

const FilterBar: React.FC<FilterBarProps> = ({
    selectedMonth,
    onMonthChange,
    selectedUnit,
    onUnitChange,
    selectedLocation,
    onLocationChange
}) => {
    const months = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];

    const units = ['Unidades de Geração', 'MW', 'GW', 'kW'];
    const locations = ['Selecione um Local', 'João Pessoa', 'São José de Sabugi', 'Areia do Breianas', 'São Mamede', 'Santa Luzia', 'Coremas', 'Patos', 'Souza'];

    return (
        <div className="filter-bar">
            <div className="lorem-ipsum">
                <h2>LOREM IPSUM</h2>
            </div>
            
            <div className="filter-controls">
                <div className="dropdown-controls">
                    <select 
                        value={selectedMonth} 
                        onChange={(e) => onMonthChange(e.target.value)}
                        className="filter-dropdown"
                    >
                        <option>Selecione um mês</option>
                        {months.map(month => (
                            <option key={month} value={month}>{month}</option>
                        ))}
                    </select>
                    
                    <select 
                        value={selectedUnit} 
                        onChange={(e) => onUnitChange(e.target.value)}
                        className="filter-dropdown"
                    >
                        {units.map(unit => (
                            <option key={unit} value={unit}>{unit}</option>
                        ))}
                    </select>
                    
                    <select 
                        value={selectedLocation} 
                        onChange={(e) => onLocationChange(e.target.value)}
                        className="filter-dropdown"
                    >
                        {locations.map(location => (
                            <option key={location} value={location}>{location}</option>
                        ))}
                    </select>
                </div>
            </div>
        </div>
    );
};

export default FilterBar;
