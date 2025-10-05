import React from 'react';
import './ActionBar.css';

interface ActionBarProps {
    onGenerateReport: () => void;
}

const ActionBar: React.FC<ActionBarProps> = ({ onGenerateReport }) => {
    return (
        <div className="action-bar-container">
            <button className="report-button" onClick={onGenerateReport}>
                Create Report
            </button>
        </div>
    );
};

export default ActionBar;