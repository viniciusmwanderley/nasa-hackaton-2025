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
  dayInitial: string; // S, T, Q, Q, S, S, D
  date: string; // YYYY-MM-DD
  temperature?: number; // Temperatura específica quando horário definido
  minTemperature?: number; // Temperatura mínima quando horário não definido
  maxTemperature?: number; // Temperatura máxima quando horário não definido
  condition: 'sunny' | 'cloudy' | 'rainy' | 'hot' | 'cold' | 'windy';
  probability?: number; // Probabilidade de condições adversas
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
  selectedDate: string; // YYYY-MM-DD
  selectedTime: TimeSelection | null; // null quando horário não definido
  weatherData: WeatherData | null;
  forecast: DayForecast[];
  precipitationData: PrecipitationData[];
  calendar: CalendarData;
  isLoading: boolean;
  error: string | null;
}

// Configurações da aplicação
export interface AppConfig {
  windowDays: number;
  baselineStart: number;
  baselineEnd: number;
  units: 'metric' | 'imperial';
  detail: 'lean' | 'full';
}
