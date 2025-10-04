// Utilitários para integração com a API do backend

import type { RiskRequest, RiskResponseLean } from '../types/api';
import type { Location } from '../types/app';

// Configuração da API
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Função para fazer requisições à API
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// Função para buscar dados de risco meteorológico
export const fetchWeatherRisk = async (request: RiskRequest): Promise<RiskResponseLean> => {
  return apiRequest<RiskResponseLean>('/risk', {
    method: 'POST',
    body: JSON.stringify(request),
  });
};

// Função para verificar saúde da API
export const checkApiHealth = async (): Promise<{ status: string; version?: string; uptime_s?: number }> => {
  return apiRequest<{ status: string; version?: string; uptime_s?: number }>('/health');
};

// Função para converter coordenadas em localização (mock - futuramente usar API de geocoding)
export const geocodeLocation = async (query: string): Promise<Location[]> => {
  // TODO: Implementar integração com API de geocoding real
  // Por enquanto, retorna localizações mockadas
  
  await new Promise(resolve => setTimeout(resolve, 500)); // Simula delay de rede
  
  const mockLocations: { [key: string]: Location } = {
    'fortaleza': {
      latitude: -3.7319,
      longitude: -38.5267,
      city: 'FORTALEZA',
      state: 'CE',
      country: 'Brasil'
    },
    'recife': {
      latitude: -8.0476,
      longitude: -34.8770,
      city: 'RECIFE',
      state: 'PE',
      country: 'Brasil'
    },
    'natal': {
      latitude: -5.7945,
      longitude: -35.2110,
      city: 'NATAL',
      state: 'RN',
      country: 'Brasil'
    },
    'joão pessoa': {
      latitude: -7.1195,
      longitude: -34.8473,
      city: 'JOÃO PESSOA',
      state: 'PB',
      country: 'Brasil'
    },
    'salvador': {
      latitude: -12.9714,
      longitude: -38.5014,
      city: 'SALVADOR',
      state: 'BA',
      country: 'Brasil'
    },
    'brasília': {
      latitude: -15.7942,
      longitude: -47.8822,
      city: 'BRASÍLIA',
      state: 'DF',
      country: 'Brasil'
    }
  };

  const searchLower = query.toLowerCase();
  const results: Location[] = [];

  // Busca exata
  if (mockLocations[searchLower]) {
    results.push(mockLocations[searchLower]);
  } else {
    // Busca parcial
    Object.entries(mockLocations).forEach(([key, location]) => {
      if (key.includes(searchLower) || location.city.toLowerCase().includes(searchLower)) {
        results.push(location);
      }
    });
  }

  return results;
};

// Função para converter dados da API em formato do app
export const transformApiDataToAppState = (apiData: RiskResponseLean) => {
  // Determina a condição predominante baseada nas probabilidades
  const probabilities = {
    hot: apiData.very_hot.probability,
    cold: apiData.very_cold.probability,
    windy: apiData.very_windy.probability,
    wet: apiData.very_wet.probability
  };

  type ConditionType = 'hot' | 'cold' | 'windy' | 'wet' | 'normal';
  
  const maxCondition = Object.entries(probabilities).reduce((max, [condition, prob]) => 
    prob > max.probability ? { condition: condition as ConditionType, probability: prob } : max,
    { condition: 'normal' as ConditionType, probability: 0 }
  );

  // Gera descrição baseada na condição
  const descriptions = {
    hot: "Muito calor! Use roupas leves, procure sombra e mantenha-se hidratado.",
    cold: "Muito frio! Vista roupas quentes e proteja-se do vento.",
    windy: "Muito vento! Cuidado com objetos soltos e evite atividades ao ar livre.",
    wet: "Muita chuva! Leve guarda-chuva e evite áreas de alagamento.",
    normal: "Condições climáticas normais para a região e época."
  };

  return {
    weatherData: {
      temperature: Math.round(Math.random() * 15 + 20), // Temporário - usar dados reais quando disponível
      description: descriptions[maxCondition.condition],
      rainChance: Math.round(apiData.very_wet.probability * 100),
      city: "Local Selecionado", // Será substituído pelo contexto
      state: "", // Será substituído pelo contexto
      condition: maxCondition.condition,
      humidity: Math.round(Math.random() * 40 + 40), // 40-80%
      windSpeed: Math.round(Math.random() * 20 + 5) // 5-25 m/s
    },
    probabilities: {
      hot: apiData.very_hot,
      cold: apiData.very_cold,
      windy: apiData.very_windy,
      wet: apiData.very_wet,
      anyAdverse: apiData.any_adverse
    },
    metadata: {
      sampleStatistics: apiData.sample_statistics,
      thresholds: apiData.thresholds
    }
  };
};

// Função para criar request da API baseado no estado do app
export const createApiRequest = (
  location: Location,
  selectedDate: string,
  selectedTime: { hour: number; formatted: string },
  config: { windowDays: number; baselineStart: number; baselineEnd: number }
): RiskRequest => {
  return {
    lat: location.latitude,
    lon: location.longitude,
    date_local: selectedDate,
    hour_local: selectedTime.formatted,
    window_days: config.windowDays,
    baseline_start: config.baselineStart,
    baseline_end: config.baselineEnd,
    detail: 'lean',
    units: 'metric'
  };
};
