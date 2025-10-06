import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';

interface FilterContextType {
  localDate: string;
  setLocalDate: (date: string) => void;
}

const FilterContext = createContext<FilterContextType | undefined>(undefined);

interface FilterProviderProps {
  children: ReactNode;
}

export const FilterProvider: React.FC<FilterProviderProps> = ({ children }) => {
  const [localDate, setLocalDate] = useState(new Date().toISOString().split('T')[0]);

  const value: FilterContextType = {
    localDate,
    setLocalDate
  };

  return (
    <FilterContext.Provider value={value}>
      {children}
    </FilterContext.Provider>
  );
};

export const useFilter = () => {
  const context = useContext(FilterContext);
  if (context === undefined) {
    throw new Error('useFilter must be used within a FilterProvider');
  }
  return context;
};