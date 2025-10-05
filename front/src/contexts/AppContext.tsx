import React, { createContext, useContext, useReducer } from 'react';
import type { ReactNode } from 'react';
import type { AppState, AppConfig, Location, WeatherData, DayForecast, PrecipitationData, CalendarData, TimeSelection } from '../types';
import type { RiskResponseLean } from '../types/api';

// Ações do reducer
type AppAction =
  | { type: 'SET_LOCATION'; payload: Location }
  | { type: 'SET_SELECTED_DATE'; payload: string }
  | { type: 'SET_SELECTED_TIME'; payload: TimeSelection | null }
  | { type: 'SET_WEATHER_DATA'; payload: WeatherData }
  | { type: 'SET_FORECAST'; payload: DayForecast[] }
  | { type: 'SET_PRECIPITATION_DATA'; payload: PrecipitationData[] }
  | { type: 'SET_CALENDAR'; payload: CalendarData }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'UPDATE_FROM_API'; payload: RiskResponseLean }
  | { type: 'RESET_STATE' };

// Estado inicial
const getCurrentDate = () => {
  const today = new Date();
  return today.toISOString().split('T')[0];
};



const initialState: AppState = {
  location: {
    latitude: -7.1195,
    longitude: -34.8473,
    city: "JOÃO PESSOA",
    state: "PB",
    country: "Brasil"
  },
  selectedDate: getCurrentDate(), // Atualiza para usar a data atual
  selectedTime: null, // Inicializa sem horário definido
  weatherData: {
    temperature: 28,
    description: "Que calorão! Procure abrigo fresco, use roupas claras e beba água.",
    rainChance: 15,
    city: "JOÃO PESSOA",
    state: "PB",
    condition: "hot"
  },
  forecast: [
    { dayInitial: 'S', date: getCurrentDate(), minTemperature: 24, maxTemperature: 30, condition: 'sunny' },
    { dayInitial: 'T', date: getCurrentDate(), minTemperature: 22, maxTemperature: 28, condition: 'cloudy' },
    { dayInitial: 'Q', date: getCurrentDate(), minTemperature: 20, maxTemperature: 26, condition: 'rainy' },
    { dayInitial: 'Q', date: getCurrentDate(), minTemperature: 21, maxTemperature: 27, condition: 'sunny' },
    { dayInitial: 'S', date: getCurrentDate(), minTemperature: 23, maxTemperature: 29, condition: 'sunny' },
    { dayInitial: 'S', date: getCurrentDate(), minTemperature: 25, maxTemperature: 31, condition: 'sunny' },
    { dayInitial: 'D', date: getCurrentDate(), minTemperature: 26, maxTemperature: 32, condition: 'sunny' }
  ],
  precipitationData: Array.from({ length: 31 }, () => ({
    date: getCurrentDate(),
    value: Math.floor(Math.random() * 90) + 5
  })),
  calendar: {
    currentMonth: new Date().getMonth(),
    currentYear: new Date().getFullYear(),
    selectedDate: getCurrentDate(),
    availableDates: []
  },
  isLoading: false,
  error: null
};

// Configuração padrão
const defaultConfig: AppConfig = {
  windowDays: 7,
  baselineStart: 2001,
  baselineEnd: 2025,
  units: 'metric',
  detail: 'lean'
};

// Reducer
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_LOCATION':
      return { ...state, location: action.payload };
    
    case 'SET_SELECTED_DATE':
      return { 
        ...state, 
        selectedDate: action.payload,
        calendar: {
          ...state.calendar,
          selectedDate: action.payload
        }
      };
    
    case 'SET_SELECTED_TIME':
      return { ...state, selectedTime: action.payload };
    
    case 'SET_WEATHER_DATA':
      return { ...state, weatherData: action.payload };
    
    case 'SET_FORECAST':
      return { ...state, forecast: action.payload };
    
    case 'SET_PRECIPITATION_DATA':
      return { ...state, precipitationData: action.payload };
    
    case 'SET_CALENDAR':
      return { ...state, calendar: action.payload };
    
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    
    case 'UPDATE_FROM_API':
      // Atualiza o estado com dados da API
      const apiData = action.payload;
      return {
        ...state,
        location: {
          ...state.location,
          latitude: apiData.latitude,
          longitude: apiData.longitude
        },
        weatherData: {
          ...state.weatherData!,
          temperature: Math.round(Math.random() * 15 + 20), // Temporário até integrar com dados reais
          condition: apiData.very_hot.probability > 0.5 ? 'hot' : 
                    apiData.very_cold.probability > 0.5 ? 'cold' :
                    apiData.very_windy.probability > 0.5 ? 'windy' :
                    apiData.very_wet.probability > 0.5 ? 'wet' : 'normal'
        },
        isLoading: false,
        error: null
      };
    
    case 'RESET_STATE':
      return initialState;
    
    default:
      return state;
  }
}

// Context
interface AppContextType {
  state: AppState;
  config: AppConfig;
  dispatch: React.Dispatch<AppAction>;
  // Ações auxiliares
  setLocation: (location: Location) => void;
  setSelectedDate: (date: string) => void;
  setSelectedTime: (time: TimeSelection | null) => void;
  updateCalendarMonth: (month: number, year: number) => void;
  fetchWeatherData: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider
interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Ações auxiliares
  const setLocation = (location: Location) => {
    dispatch({ type: 'SET_LOCATION', payload: location });
  };

  const setSelectedDate = (date: string) => {
    dispatch({ type: 'SET_SELECTED_DATE', payload: date });
  };

  const setSelectedTime = (time: TimeSelection | null) => {
    dispatch({ type: 'SET_SELECTED_TIME', payload: time });
  };

  const updateCalendarMonth = (month: number, year: number) => {
    const newCalendar: CalendarData = {
      ...state.calendar,
      currentMonth: month,
      currentYear: year
    };
    dispatch({ type: 'SET_CALENDAR', payload: newCalendar });
  };

  const fetchWeatherData = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      // TODO: Implementar chamada real para a API quando estiver pronta
      // Por enquanto, simula uma requisição
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Dados simulados baseados na estrutura da API
      const mockApiResponse: RiskResponseLean = {
        latitude: state.location.latitude,
        longitude: state.location.longitude,
        target_date: state.selectedDate,
        target_hour: state.selectedTime?.hour ?? 12, // Usa 12h como padrão quando não definido
        very_hot: {
          probability: Math.random(),
          confidence_interval: {
            lower: 0.1,
            upper: 0.9,
            level: 0.95,
            width: 0.8
          },
          positive_samples: 50
        },
        very_cold: {
          probability: Math.random(),
          confidence_interval: {
            lower: 0.1,
            upper: 0.9,
            level: 0.95,
            width: 0.8
          },
          positive_samples: 30
        },
        very_windy: {
          probability: Math.random(),
          confidence_interval: {
            lower: 0.1,
            upper: 0.9,
            level: 0.95,
            width: 0.8
          },
          positive_samples: 20
        },
        very_wet: {
          probability: Math.random(),
          confidence_interval: {
            lower: 0.1,
            upper: 0.9,
            level: 0.95,
            width: 0.8
          },
          positive_samples: 40
        },
        any_adverse: {
          probability: Math.random(),
          confidence_interval: {
            lower: 0.1,
            upper: 0.9,
            level: 0.95,
            width: 0.8
          },
          positive_samples: 80
        },
        sample_statistics: {
          total_samples: 1000,
          years_with_data: 24,
          coverage_adequate: true,
          timezone_iana: "America/Fortaleza"
        },
        thresholds: {
          very_hot_c: 35,
          very_cold_c: 10,
          very_windy_ms: 15,
          very_wet_mm_per_day: 50
        }
      };

      dispatch({ type: 'UPDATE_FROM_API', payload: mockApiResponse });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: 'Erro ao buscar dados meteorológicos' });
    }
  };

  const value: AppContextType = {
    state,
    config: defaultConfig,
    dispatch,
    setLocation,
    setSelectedDate,
    setSelectedTime,
    updateCalendarMonth,
    fetchWeatherData
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

// Hook customizado
export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
