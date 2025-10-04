import React from 'react';
import './RenewableEnergyCard.css';

const RenewableEnergyCard: React.FC = () => {
    return (
        <div className="energy-card">
            <div className="energy-content">
                <div className="energy-text">
                    <h3 className="energy-title">Explore o poder das energias renováveis</h3>
                    <p className="energy-subtitle">Descubra onde investir no futuro limpo</p>
                    <button className="access-button">Acessar Painel</button>
                </div>
                
                <div className="energy-illustration-area">
                    <img
                        src="/object.png"
                        alt="Painel de energias renováveis"
                    />
                </div>

            </div>
        </div>
    );
};

export default RenewableEnergyCard;