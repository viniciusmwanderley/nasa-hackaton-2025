import React from 'react';
import './PlaceholderCards.css';

const PlaceholderCards: React.FC = () => {
    const cards = Array.from({ length: 5 }, (_, index) => ({
        id: index + 1,
        title: `Card ${index + 1}`,
    }));

    return (
        <div className="placeholder-cards">
            {cards.map((card) => (
                <div key={card.id} className="placeholder-card">
                    <div className="placeholder-content">
                        {/* Conteúdo placeholder - pode ser substituído posteriormente */}
                    </div>
                </div>
            ))}
        </div>
    );
};

export default PlaceholderCards;
