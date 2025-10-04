import React from 'react';
import './ActionBar.css';

interface ActionBarProps {
    onGenerateReport: () => void;
    onExport: () => void;
}

const ActionBar: React.FC<ActionBarProps> = ({ onGenerateReport, onExport }) => {
    return (
        <div className="action-bar-container">
            <button className="report-button" onClick={onGenerateReport}>
                Gerar Relatório
            </button>
            <button className="export-button" onClick={onExport}>
                Exportar
            </button>
        </div>
    );
};

export default ActionBar;