import React, { createContext, useContext, useReducer } from 'react';
import type { ReactNode } from 'react';
import type { AppState, AppConfig, Location, WeatherData, DayForecast, PrecipitationData, CalendarData, TimeSelection } from '../types';
import type { RiskResponseLean, WeatherAnalyzeResponse } from '../types/api';
import { getTimezoneFromLocationSync } from '../utils/timezone';

// Reducer actions
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
  | { type: 'UPDATE_FROM_WEATHER_API'; payload: WeatherAnalyzeResponse }
  | { type: 'RESET_STATE' };

// Initial state
const getCurrentDate = (location?: Location) => {
  if (location) {
    const timezone = getTimezoneFromLocationSync(location);
    const now = new Date();
    
    const formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone: timezone,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
    
    return formatter.format(now);
  }
  
  const today = new Date();
  return today.toISOString().split('T')[0];
};



const initialLocation: Location = {
  latitude: -7.1195,
  longitude: -34.8473,
  city: "JOÃO PESSOA",
  state: "PB",
  country: "Brasil"
};

const initialState: AppState = {
  location: initialLocation,
  selectedDate: getCurrentDate(initialLocation), 
  selectedTime: null,
  weatherData: null, 
  forecast: [],
  precipitationData: [],
  calendar: {
    currentMonth: new Date().getMonth(),
    currentYear: new Date().getFullYear(),
    selectedDate: getCurrentDate(initialLocation), 
    availableDates: []
  },
  isLoading: true, 
  error: null,
  apiData: null
};

// Default configuration
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
      { const apiData = action.payload;
      return {
        ...state,
        location: {
          ...state.location,
          latitude: apiData.latitude,
          longitude: apiData.longitude
        },
        weatherData: {
          ...state.weatherData!,
          temperature: Math.round(Math.random() * 15 + 20), 
          condition: apiData.very_hot.probability > 0.5 ? 'hot' : 
                    apiData.very_cold.probability > 0.5 ? 'cold' :
                    apiData.very_windy.probability > 0.5 ? 'windy' :
                    apiData.very_wet.probability > 0.5 ? 'wet' : 'normal'
        },
        isLoading: false,
        error: null
      }; }

    case 'UPDATE_FROM_WEATHER_API':
      try {
        const weatherData = action.payload;
        
        if (!weatherData || !weatherData.results || !Array.isArray(weatherData.results)) {
          console.error('Invalid API data:', weatherData);
          return {
            ...state,
            error: 'Invalid API data received',
            isLoading: false
          };
        }
      
      const selectedDateResult = weatherData.results.find(result => 
        result.datetime.split('T')[0] === state.selectedDate
      ) || weatherData.results[Math.floor(weatherData.results.length / 2)]; 
      
      
      let condition: 'hot' | 'cold' | 'windy' | 'wet' | 'normal' = 'normal';
      const classifications = weatherData.classifications;
            
      if (classifications.very_hot_temp_percentile > 60) condition = 'hot';
      else if (classifications.very_windy_percentile > 65) condition = 'windy';
      else if (classifications.very_wet_probability > 0.15 || classifications.rain_probability > 0.4) condition = 'wet';

      const temperature = Math.round(selectedDateResult.parameters.T2M.value);
      const rainChance = Math.round(classifications.rain_probability * 100);
            
      const updatedWeatherData: WeatherData = {
        temperature,
        description: condition === 'hot' ? `Temperatura de ${temperature}°C! Procure abrigo fresco, use roupas claras e beba água.` :
                    condition === 'windy' ? `Ventos fortes detectados! Cuidado com objetos soltos. Temperatura: ${temperature}°C` :
                    condition === 'wet' ? `${rainChance}% de chance de chuva! Leve guarda-chuva. Temperatura: ${temperature}°C` :
                    `Clima agradável de ${temperature}°C para atividades ao ar livre.`,
        rainChance,
        city: state.location.city,
        state: state.location.state,
        condition
      };

      const isHourlyData = weatherData.meta.granularity === 'hourly';

      const forecast: DayForecast[] = weatherData.results.slice(0, 7).map((result, index) => {
        try {
          const date = result.datetime.split('T')[0];
          const dayNames = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];
          
          const baseData = {
            dayInitial: dayNames[index % 7],
            date,
            condition: (result.parameters?.PRECTOTCORR?.value || 0) > 5 ? 'rainy' :
                      (result.parameters?.T2M?.value || 0) > 30 ? 'sunny' :
                      (result.parameters?.CLOUD_AMT?.value || 0) > 50 ? 'cloudy' : 'sunny'
          } as DayForecast;

          if (isHourlyData) {
            if (result.parameters?.T2M?.value !== undefined) {
              baseData.temperature = Math.round(result.parameters.T2M.value);
            } else {
              baseData.temperature = 0; 
            }
          } else {
            if (result.parameters?.T2M_MIN?.value !== undefined && result.parameters?.T2M_MAX?.value !== undefined) {
              baseData.minTemperature = Math.round(result.parameters.T2M_MIN.value);
              baseData.maxTemperature = Math.round(result.parameters.T2M_MAX.value);
            } else {
              baseData.minTemperature = 0; 
              baseData.maxTemperature = 0;
            }
          }

          return baseData;
        } catch (error) {
          console.error(`Error processing result ${index + 1}:`, error);
          return {
            dayInitial: ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'][index % 7],
            date: new Date().toISOString().split('T')[0],
            temperature: isHourlyData ? 0 : undefined,
            minTemperature: isHourlyData ? undefined : 0,
            maxTemperature: isHourlyData ? undefined : 0,
            condition: 'sunny'
          } as DayForecast;
        }
      });

      
      const precipitationData: PrecipitationData[] = weatherData.results.map(result => ({
        date: result.datetime.split('T')[0],
        value: result.parameters.PRECTOTCORR.value
      }));

        return {
          ...state,
          weatherData: updatedWeatherData,
          forecast,
          precipitationData,
          apiData: {
            classifications: weatherData.classifications,
            selectedDayData: selectedDateResult,
            allResults: weatherData.results
          },
          isLoading: false,
          error: null
        };
      } catch (error) {
        console.error('Error processing weather data:', error);
        return {
          ...state,
          error: 'Error processing weather data',
          isLoading: false
        };
      }
    
    case 'RESET_STATE':
      return initialState;
    
    default:
      return state;
  }
}

interface AppContextType {
  state: AppState;
  config: AppConfig;
  dispatch: React.Dispatch<AppAction>;
  setLocation: (location: Location) => void;
  setSelectedDate: (date: string) => void;
  setSelectedTime: (time: TimeSelection | null) => void;
  updateCalendarMonth: (month: number, year: number) => void;
  fetchWeatherData: () => Promise<void>;
  analyzeWeather: (customLocation?: Location, customDate?: string, customTime?: TimeSelection | null) => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider
interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  React.useEffect(() => {
    callWeatherAnalyzeAPI(initialState.location, initialState.selectedDate, initialState.selectedTime);
  }, []);

  const callWeatherAnalyzeAPI = async (location: Location, selectedDate: string, selectedTime: TimeSelection | null) => {    
    const timezone = getTimezoneFromLocationSync(location);
    
    // Formatting center_datetime
    const centerDatetime = selectedTime
      ? `${selectedDate}T${selectedTime.formatted}:00Z`
      : `${selectedDate}T00:00:00Z`;

    const params = {
      latitude: location.latitude,
      longitude: location.longitude,
      center_datetime: centerDatetime,
      target_timezone: timezone,
      days_before: 3,
      days_after: 3,
      granularity: selectedTime ? 'hourly' : 'daily',
      window_days: 7,
      ...(selectedTime && {
        start_year: 2015,
        hourly_chunk_years: 5
      })
    };

    try {
      const response = await fetch('https://nasa-hackaton-2025-ten.vercel.app/weather/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data: WeatherAnalyzeResponse = await response.json();

      // Process and update the data
      dispatch({ type: 'UPDATE_FROM_WEATHER_API', payload: data });
      dispatch({ type: 'SET_LOADING', payload: false });

    } catch (error) {
      console.error('API Error:', error);
      dispatch({ type: 'SET_LOADING', payload: false });
      dispatch({ type: 'SET_ERROR', payload: 'Error loading data. Please try again.' });
    }
  };

  // Auxiliary actions
  const setLocation = (location: Location) => {
    dispatch({ type: 'SET_LOCATION', payload: location });
  };

  const setSelectedDate = (date: string) => {    
    dispatch({ type: 'SET_SELECTED_DATE', payload: date });
  };

  const setSelectedTime = (time: TimeSelection | null) => {    
    dispatch({ type: 'SET_SELECTED_TIME', payload: time });
  };

  const analyzeWeather = async (customLocation?: Location, customDate?: string, customTime?: TimeSelection | null) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    
    const locationToUse = customLocation ?? state.location;
    const dateToUse = customDate ?? state.selectedDate;
    const timeToUse = customTime !== undefined ? customTime : state.selectedTime;
    
    await callWeatherAnalyzeAPI(locationToUse, dateToUse, timeToUse);
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
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockApiResponse: RiskResponseLean = {
        latitude: state.location.latitude,
        longitude: state.location.longitude,
        target_date: state.selectedDate,
        target_hour: state.selectedTime?.hour ?? 12, 
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
      console.error('Error fetching weather data:', error);
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
    fetchWeatherData,
    analyzeWeather
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook
// eslint-disable-next-line react-refresh/only-export-components
export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
