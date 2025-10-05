import React from 'react';
import './Header.css';

const Header: React.FC = () => {
  return (
    <div className="app-header">
      <div className="header-container">
        <div className="header-brand">
          <div className="climadata-logo">
            <img src="/weatherdata.png" alt="CLIMADATA" className="logo-image" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Header;
