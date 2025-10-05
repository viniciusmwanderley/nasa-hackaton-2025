import React from 'react';
import './RenewableEnergyCard.css';

const RenewableEnergyCard: React.FC = () => {
    return (
        <div className="energy-card">
            <div className="energy-content">
                <div className="energy-text">
                    <h3 className="energy-title">Explore the potential of renewable energy</h3>
                    <p className="energy-subtitle">Discover where to invest in a clean future</p>
                </div>
                
                <div className="energy-illustration-area">
                    <img
                        src="/object.png"
                        alt="Painel de energias renováveis"
                    />
                </div>
                <button className="access-button">Access Panel</button>
            </div>
        </div>
    );
};

export default RenewableEnergyCard;