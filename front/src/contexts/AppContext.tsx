import React, { createContext, useContext, useReducer } from 'react';
import type { ReactNode } from 'react';
import type { AppState, AppConfig, Location, WeatherData, DayForecast, PrecipitationData, CalendarData, TimeSelection } from '../types';
import type { RiskResponseLean, WeatherAnalyzeResponse } from '../types/api';
import { getTimezoneFromLocationSync } from '../utils/timezone';

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
  | { type: 'UPDATE_FROM_WEATHER_API'; payload: WeatherAnalyzeResponse }
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
  selectedDate: getCurrentDate(),
  selectedTime: null,
  weatherData: null, // Inicia sem dados
  forecast: [],
  precipitationData: [],
  calendar: {
    currentMonth: new Date().getMonth(),
    currentYear: new Date().getFullYear(),
    selectedDate: getCurrentDate(),
    availableDates: []
  },
  isLoading: true, // Inicia em loading
  error: null,
  apiData: null
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

    case 'UPDATE_FROM_WEATHER_API':
      try {
        // Processa dados da API /weather/analyze/
        const weatherData = action.payload;
        
        if (!weatherData || !weatherData.results || !Array.isArray(weatherData.results)) {
          console.error('Dados da API inválidos:', weatherData);
          return {
            ...state,
            error: 'Dados inválidos recebidos da API',
            isLoading: false
          };
        }
      
      // Encontra o resultado para o dia selecionado
      console.log('Procurando dados para a data:', state.selectedDate);
      console.log('Datas disponíveis:', weatherData.results.map(r => r.datetime.split('T')[0]));
      
      const selectedDateResult = weatherData.results.find(result => 
        result.datetime.split('T')[0] === state.selectedDate
      ) || weatherData.results[Math.floor(weatherData.results.length / 2)]; // Fallback para o meio da lista
      
      console.log('Dados selecionados para o dia:', selectedDateResult);

      // Mapeia condição baseada nas classificações
      let condition: 'hot' | 'cold' | 'windy' | 'wet' | 'normal' = 'normal';
      const classifications = weatherData.classifications;
      
      console.log('=== PROCESSANDO CLASSIFICAÇÕES ===');
      console.log('Percentil de calor:', classifications.very_hot_temp_percentile);
      console.log('Percentil de vento:', classifications.very_windy_percentile);
      console.log('Probabilidade de chuva forte:', classifications.very_wet_probability);
      console.log('Probabilidade de chuva geral:', classifications.rain_probability);
      
      if (classifications.very_hot_temp_percentile > 60) condition = 'hot';
      else if (classifications.very_windy_percentile > 65) condition = 'windy';
      else if (classifications.very_wet_probability > 0.15 || classifications.rain_probability > 0.4) condition = 'wet';

      // Atualiza weather data com dados reais
      const temperature = Math.round(selectedDateResult.parameters.T2M.value);
      const rainChance = Math.round(classifications.rain_probability * 100);
      const humidity = Math.round(selectedDateResult.parameters.RH2M.value);
      
      console.log('=== DADOS PROCESSADOS ===');
      console.log('Temperatura:', temperature + '°C');
      console.log('Chance de chuva:', rainChance + '%');
      console.log('Umidade:', humidity + '%');
      console.log('Condição:', condition);
      
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

      // Gera forecast com dados reais baseado na granularidade
      const isHourlyData = weatherData.meta.granularity === 'hourly';
      console.log('Tipo de dados:', isHourlyData ? 'Horário específico' : 'Diário (min/max)');
      console.log('Quantidade de resultados recebidos:', weatherData.results.length);
      
      const forecast: DayForecast[] = weatherData.results.slice(0, 7).map((result, index) => {
        try {
          const date = result.datetime.split('T')[0];
          const dayNames = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];
          
          console.log(`Processando resultado ${index + 1}:`, {
            datetime: result.datetime,
            T2M: result.parameters?.T2M?.value,
            T2M_MIN: result.parameters?.T2M_MIN?.value,
            T2M_MAX: result.parameters?.T2M_MAX?.value
          });
          
          const baseData = {
            dayInitial: dayNames[index % 7],
            date,
            condition: (result.parameters?.PRECTOTCORR?.value || 0) > 5 ? 'rainy' :
                      (result.parameters?.T2M?.value || 0) > 30 ? 'sunny' :
                      (result.parameters?.CLOUD_AMT?.value || 0) > 50 ? 'cloudy' : 'sunny'
          } as DayForecast;

          if (isHourlyData) {
            // Para dados horários, usa temperatura única
            if (result.parameters?.T2M?.value !== undefined) {
              baseData.temperature = Math.round(result.parameters.T2M.value);
              console.log(`Dia ${index + 1}: ${baseData.temperature}°C (horário específico)`);
            } else {
              console.error(`Temperatura T2M não encontrada para o dia ${index + 1}`);
              baseData.temperature = 0; // Fallback
            }
          } else {
            // Para dados diários, usa min/max
            if (result.parameters?.T2M_MIN?.value !== undefined && result.parameters?.T2M_MAX?.value !== undefined) {
              baseData.minTemperature = Math.round(result.parameters.T2M_MIN.value);
              baseData.maxTemperature = Math.round(result.parameters.T2M_MAX.value);
              console.log(`Dia ${index + 1}: ${baseData.minTemperature}°C - ${baseData.maxTemperature}°C (min/max)`);
            } else {
              console.error(`Temperaturas min/max não encontradas para o dia ${index + 1}`);
              baseData.minTemperature = 0; // Fallback
              baseData.maxTemperature = 0; // Fallback
            }
          }

          return baseData;
        } catch (error) {
          console.error(`Erro ao processar resultado ${index + 1}:`, error);
          // Retorna dados padrão em caso de erro
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

      // Gera dados de precipitação
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
        console.error('Erro ao processar dados da API:', error);
        return {
          ...state,
          error: 'Erro ao processar dados meteorológicos',
          isLoading: false
        };
      }
    
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
  setLocation: (location: Location) => Promise<void>;
  setSelectedDate: (date: string) => Promise<void>;
  setSelectedTime: (time: TimeSelection | null) => Promise<void>;
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

  // Carrega dados iniciais quando a aplicação inicia
  React.useEffect(() => {
    console.log('🚀 Iniciando aplicação - Carregando dados para João Pessoa...');
    callWeatherAnalyzeAPI(initialState.location, initialState.selectedDate, initialState.selectedTime);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Função para chamar a API weather/analyze
  const callWeatherAnalyzeAPI = async (location: Location, selectedDate: string, selectedTime: TimeSelection | null) => {
    console.log('🌤️ Buscando dados da API para:', location.city);
    
    const timezone = getTimezoneFromLocationSync(location);
    
    // Formatar center_datetime
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
      console.log('✅ Dados recebidos da API com sucesso');
      
      // Processa e atualiza os dados
      dispatch({ type: 'UPDATE_FROM_WEATHER_API', payload: data });
      dispatch({ type: 'SET_LOADING', payload: false });

    } catch (error) {
      console.error('❌ Erro na API:', error);
      dispatch({ type: 'SET_LOADING', payload: false });
      dispatch({ type: 'SET_ERROR', payload: 'Erro ao carregar dados. Tente novamente.' });
    }
  };

  // Ações auxiliares
  const setLocation = async (location: Location) => {
    console.log('🚀 Mudando localização para:', location.city);
    
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_LOCATION', payload: location });
    
    await callWeatherAnalyzeAPI(location, state.selectedDate, state.selectedTime);
  };

  const setSelectedDate = async (date: string) => {
    console.log('📅 Mudando data para:', date);
    
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_SELECTED_DATE', payload: date });
    
    await callWeatherAnalyzeAPI(state.location, date, state.selectedTime);
  };

  const setSelectedTime = async (time: TimeSelection | null) => {
    console.log('⏰ Mudando horário para:', time?.formatted || 'All Day');
    
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_SELECTED_TIME', payload: time });
    
    await callWeatherAnalyzeAPI(state.location, state.selectedDate, time);
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
