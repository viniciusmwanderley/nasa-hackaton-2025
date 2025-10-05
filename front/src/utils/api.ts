// utils/api.ts
import type { Location } from '../types/app';

const OPENWEATHER_API_KEY = import.meta.env.VITE_OPENWEATHER_API_KEY;

// Busca cidade -> coordenadas usando API de geocodificação do OpenWeather
export const geocodeLocation = async (query: string): Promise<Location[]> => {
  const url = `http://api.openweathermap.org/geo/1.0/direct?q=${encodeURIComponent(query)}&limit=1&appid=${OPENWEATHER_API_KEY}`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Erro HTTP: ${response.statusText}`);

    const data = await response.json();

    if (!Array.isArray(data) || data.length === 0) {
      console.warn('Nenhum resultado encontrado para:', query);
      return [];
    }

    console.log('URL da requisição:', url);
    console.log('Dados recebidos:', data);

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
    return [];
  }
};
