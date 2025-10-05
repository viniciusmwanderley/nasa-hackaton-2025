import { useState, useEffect, useCallback } from 'react';
import { fetchEnergyData, fetchMultipleEnergyData, processEnergyData, CITY_COORDINATES } from '../utils/api';
import type { ProcessedCityEnergyData } from '../types/api';

type CityKey = keyof typeof CITY_COORDINATES;

interface UseEnergyDataReturn {
  selectedCityData: ProcessedCityEnergyData | null;
  multiCityData: ProcessedCityEnergyData[];
  loading: boolean;
  error: string | null;
  selectedCity: string;
  selectedMonth: string;
  setSelectedCity: (city: string) => void;
  setSelectedMonth: (month: string) => void;
  refreshData: () => void;
}

export const useEnergyData = (
  initialCity: string = 'fortaleza',
  initialCities: string[] = ['fortaleza', 'salvador', 'recife', 'sao-paulo', 'rio-de-janeiro']
): UseEnergyDataReturn => {
  const [selectedCityData, setSelectedCityData] = useState<ProcessedCityEnergyData | null>(null);
  const [multiCityData, setMultiCityData] = useState<ProcessedCityEnergyData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCity, setSelectedCity] = useState(initialCity);
  const [selectedMonth, setSelectedMonth] = useState('ANN');

  // Função para carregar dados de uma cidade específica
  const loadSingleCityData = useCallback(async (cityKey: string) => {
    const cityInfo = CITY_COORDINATES[cityKey as CityKey];
    if (!cityInfo) {
      setError(`Cidade não encontrada: ${cityKey}`);
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const data = await fetchEnergyData(cityInfo.latitude, cityInfo.longitude);
      if (data) {
        const processedData = processEnergyData(data, cityInfo.name);
        setSelectedCityData(processedData);
      } else {
        setError('Erro ao carregar dados da cidade');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro desconhecido');
    } finally {
      setLoading(false);
    }
  }, []);

  // Função para carregar dados de múltiplas cidades
  const loadMultiCityData = useCallback(async (cityKeys: string[]) => {
    setLoading(true);
    setError(null);

    try {
      const locations = cityKeys
        .map(cityKey => {
          const cityInfo = CITY_COORDINATES[cityKey as CityKey];
          return cityInfo ? {
            latitude: cityInfo.latitude,
            longitude: cityInfo.longitude,
            cityName: cityInfo.name
          } : null;
        })
        .filter((location): location is NonNullable<typeof location> => location !== null);

      const data = await fetchMultipleEnergyData(locations);
      setMultiCityData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar dados das cidades');
    } finally {
      setLoading(false);
    }
  }, []);

  // Função para atualizar a cidade selecionada
  const handleCityChange = useCallback((city: string) => {
    setSelectedCity(city);
    loadSingleCityData(city);
  }, [loadSingleCityData]);

  // Função para atualizar o mês selecionado
  const handleMonthChange = useCallback((month: string) => {
    setSelectedMonth(month);
  }, []);

  // Função para recarregar todos os dados
  const refreshData = useCallback(() => {
    loadSingleCityData(selectedCity);
    loadMultiCityData(initialCities);
  }, [selectedCity, initialCities, loadSingleCityData, loadMultiCityData]);

  // Efeito para carregar dados iniciais
  useEffect(() => {
    loadSingleCityData(selectedCity);
    loadMultiCityData(initialCities);
  }, [selectedCity, initialCities, loadSingleCityData, loadMultiCityData]);

  return {
    selectedCityData,
    multiCityData,
    loading,
    error,
    selectedCity,
    selectedMonth,
    setSelectedCity: handleCityChange,
    setSelectedMonth: handleMonthChange,
    refreshData
  };
};
