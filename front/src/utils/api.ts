// utils/api.ts
import type { Location } from '../types/app';
import type { EnergyRequest, EnergyResponse, ProcessedCityEnergyData } from '../types/api';

const OPENWEATHER_API_KEY = import.meta.env.VITE_OPENWEATHER_API_KEY;
const API_BASE_URL = 'https://nasa-hackaton-2025-ten.vercel.app';

// Busca cidade -> coordenadas usando API de geocodificação do OpenWeather
export const geocodeLocation = async (query: string): Promise<Location[]> => {
  const url = `https://api.openweathermap.org/geo/1.0/direct?q=${encodeURIComponent(query)}&limit=1&appid=${OPENWEATHER_API_KEY}`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Erro HTTP: ${response.statusText}`);

    const data = await response.json();

    if (!Array.isArray(data) || data.length === 0) {
      console.warn('Nenhum resultado encontrado para:', query);
      return [];
    }


    return data.map((result: any) => {
      return {
        latitude: result.lat,
        longitude: result.lon,
        city: result.name,
        state: result.state || '',
        country: result.country || '',
      };
    });
    
  } catch (error) {
    console.error('Erro ao buscar localização:', error);
    console.error('URL da requisição:', url);
    console.log('Chave da API OpenWeather:', OPENWEATHER_API_KEY);
    return [];
  }
};

// Função para buscar dados de energia de uma cidade
export const fetchEnergyData = async (latitude: number, longitude: number): Promise<EnergyResponse | null> => {
  const url = `${API_BASE_URL}/climate-energy/analyze`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        latitude,
        longitude
      } as EnergyRequest)
    });

    if (!response.ok) {
      throw new Error(`Erro HTTP: ${response.status} - ${response.statusText}`);
    }

    const data: EnergyResponse = await response.json();
    return data;
  } catch (error) {
    console.error('Erro ao buscar dados de energia:', error);
    return null;
  }
};

// Função para buscar dados de energia de múltiplas cidades
export const fetchMultipleEnergyData = async (locations: Array<{latitude: number, longitude: number, cityName: string}>): Promise<ProcessedCityEnergyData[]> => {
  try {
    const promises = locations.map(async (location) => {
      const data = await fetchEnergyData(location.latitude, location.longitude);
      if (!data) return null;

      return processEnergyData(data, location.cityName);
    });

    const results = await Promise.all(promises);
    return results.filter((result): result is ProcessedCityEnergyData => result !== null);
  } catch (error) {
    console.error('Erro ao buscar dados de múltiplas cidades:', error);
    return [];
  }
};

// Função para processar dados da API em formato utilizável pelos componentes
export const processEnergyData = (data: EnergyResponse, cityName: string): ProcessedCityEnergyData => {
  const { climate_energy_potential, raw_nasa_metrics_monthly, location } = data;

  return {
    cityName,
    location,
    solarAnnual: climate_energy_potential.solar_kwh_per_m2.ANN,
    windAnnual: climate_energy_potential.wind_kwh_per_m2.ANN,
    solarMonthly: climate_energy_potential.solar_kwh_per_m2,
    windMonthly: climate_energy_potential.wind_kwh_per_m2,
    indicators: {
      solarIrradiance: raw_nasa_metrics_monthly.SolarIrradianceOptimal.ANN,
      optimalAngle: raw_nasa_metrics_monthly.SolarIrradianceOptimalAngle.ANN,
      airDensity: raw_nasa_metrics_monthly.SurfaceAirDensity.ANN,
      windSpeed: raw_nasa_metrics_monthly.WindSpeed50m.ANN,
    }
  };
};

// Mapeamento de nomes de meses
export const MONTH_NAMES = {
  JAN: 'Janeiro',
  FEB: 'Fevereiro', 
  MAR: 'Março',
  APR: 'Abril',
  MAY: 'Maio',
  JUN: 'Junho',
  JUL: 'Julho',
  AUG: 'Agosto',
  SEP: 'Setembro',
  OCT: 'Outubro',
  NOV: 'Novembro',
  DEC: 'Dezembro'
} as const;

// Coordenadas das principais cidades brasileiras
export const CITY_COORDINATES = {
  'fortaleza': { latitude: -3.7319, longitude: -38.5267, name: 'Fortaleza' },
  'salvador': { latitude: -12.9714, longitude: -38.5014, name: 'Salvador' },
  'recife': { latitude: -8.0476, longitude: -34.8770, name: 'Recife' },
  'sao-paulo': { latitude: -23.5505, longitude: -46.6333, name: 'São Paulo' },
  'rio-de-janeiro': { latitude: -22.9068, longitude: -43.1729, name: 'Rio de Janeiro' },
  'belo-horizonte': { latitude: -19.9161, longitude: -43.9344, name: 'Belo Horizonte' },
  'brasilia': { latitude: -15.8267, longitude: -47.9218, name: 'Brasília' },
  'curitiba': { latitude: -25.4284, longitude: -49.2733, name: 'Curitiba' },
  'porto-alegre': { latitude: -30.0346, longitude: -51.2177, name: 'Porto Alegre' },
  'manaus': { latitude: -3.1190, longitude: -60.0217, name: 'Manaus' }
} as const;
