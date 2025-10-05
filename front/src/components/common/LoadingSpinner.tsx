import React from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  text?: string;
  className?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'medium', 
  text = 'Carregando...', 
  className = '' 
}) => {
  const sizeMap = {
    small: { spinner: '20px', fontSize: '0.8rem' },
    medium: { spinner: '30px', fontSize: '0.9rem' },
    large: { spinner: '40px', fontSize: '1rem' }
  };

  const currentSize = sizeMap[size];

  return (
    <div className={`loading-container ${className}`} style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      textAlign: 'center'
    }}>
      <div 
        className="spinner" 
        style={{
          width: currentSize.spinner,
          height: currentSize.spinner,
          border: '3px solid #f3f3f3',
          borderTop: '3px solid #1976d2',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          marginBottom: '1rem'
        }}
      />
      <p style={{
        margin: '0',
        color: '#666',
        fontSize: currentSize.fontSize,
        fontWeight: '500'
      }}>
        {text}
      </p>
      
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default LoadingSpinner;
