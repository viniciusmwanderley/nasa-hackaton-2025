// Tipos para os componentes da aplicação

export interface WeatherData {
  temperature: number;
  description: string;
  rainChance: number;
  city: string;
  state: string;
  condition: 'hot' | 'cold' | 'windy' | 'wet' | 'normal';
  feelsLike?: number;
  humidity?: number;
  windSpeed?: number;
}

export interface Location {
  latitude: number;
  longitude: number;
  city: string;
  state: string;
  country: string;
}

export interface DayForecast {
  dayInitial: string;
  date: string;
  minTemperature?: number;
  maxTemperature?: number;
  temperature?: number; // Para quando horário específico está definido
  condition: 'sunny' | 'cloudy' | 'rainy';
}

export interface PrecipitationData {
  date: string; // YYYY-MM-DD
  value: number; // mm
  probability?: number;
}

export interface CalendarData {
  currentMonth: number; // 0-11
  currentYear: number;
  selectedDate: string | null; // YYYY-MM-DD
  availableDates: string[]; // Datas com dados disponíveis
}

export interface TimeSelection {
  hour?: number; // 0-23, undefined para todos os horários
  formatted: string; // "HH:00" ou "Todos os horários"
}

// Estado global da aplicação
export interface AppState {
  location: Location;
  selectedDate: string;
  selectedTime: TimeSelection | null;
  weatherData: WeatherData | null;
  forecast: DayForecast[];
  precipitationData: PrecipitationData[];
  calendar: CalendarData;
  isLoading: boolean;
  error: string | null;
  apiData?: {
    classifications: any;
    selectedDayData: any;
    allResults: any[];
  } | null;
}

// Configurações da aplicação
export interface AppConfig {
  windowDays: number;
  baselineStart: number;
  baselineEnd: number;
  units: 'metric' | 'imperial';
  detail: 'lean' | 'full';
}
