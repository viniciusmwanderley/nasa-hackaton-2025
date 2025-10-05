import React from 'react';
import './ActionBar.css';
import { utils, writeFile } from 'xlsx';

interface ActionBarProps {
    onGenerateReport: () => void;
}

const ActionBar: React.FC<ActionBarProps> = ({ onGenerateReport }) => {
    const handleCreateReport = () => {
        // Placeholder data for the CSV
        const data = [
            { Column1: 'Value1', Column2: 'Value2', Column3: 'Value3' },
            { Column1: 'Value4', Column2: 'Value5', Column3: 'Value6' },
        ];

        // Convert data to worksheet
        const worksheet = utils.json_to_sheet(data);
        const workbook = utils.book_new();
        utils.book_append_sheet(workbook, worksheet, 'Report');

        // Write workbook and trigger download
        writeFile(workbook, 'report.xlsx');
    };

    return (
        <div className="action-bar-container">
            <button className="report-button" onClick={handleCreateReport}>
                Create Report
            </button>
        </div>
    );
};

export default ActionBar;