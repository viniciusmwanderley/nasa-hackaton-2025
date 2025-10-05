// Tipos baseados na API do backend para integração futura

export interface ConfidenceInterval {
  lower: number;
  upper: number;
  level: number;
  width: number;
}

export interface ConditionProbability {
  probability: number;
  confidence_interval: ConfidenceInterval;
  positive_samples: number;
}

export interface SampleStatistics {
  total_samples: number;
  years_with_data: number;
  coverage_adequate: boolean;
  timezone_iana: string;
}

export interface ConditionThresholds {
  very_hot_c: number;
  very_cold_c: number;
  very_windy_ms: number;
  very_wet_mm_per_day: number;
}

// Resposta principal da API /risk
export interface RiskResponseLean {
  latitude: number;
  longitude: number;
  target_date: string; // YYYY-MM-DD
  target_hour: number; // 0-23
  very_hot: ConditionProbability;
  very_cold: ConditionProbability;
  very_windy: ConditionProbability;
  very_wet: ConditionProbability;
  any_adverse: ConditionProbability;
  sample_statistics: SampleStatistics;
  thresholds: ConditionThresholds;
}

// Request para a API
export interface RiskRequest {
  lat: number;
  lon: number;
  date_local: string; // YYYY-MM-DD
  hour_local: string; // HH:00
}

// Tipos para API /weather/analyze/
export interface WeatherParameter {
  value: number;
  mode: string;
  climatology_month_mean: number | null;
  model_used: string | null;
}

export interface WeatherResult {
  datetime: string;
  parameters: {
    FRSNO: WeatherParameter;
    PRECTOTCORR: WeatherParameter;
    RH2M: WeatherParameter;
    T2M: WeatherParameter;
    CLOUD_AMT: WeatherParameter;
    T2M_MIN: WeatherParameter;
    IMERG_PRECTOT: WeatherParameter;
    ALLSKY_SFC_SW_DWN: WeatherParameter;
    T2M_MAX: WeatherParameter;
    WS10M: WeatherParameter;
  };
  derived_insights: {
    heat_index_c: number;
  };
}

export interface WeatherStats {
  count: number;
  mean: number;
  median: number;
  min: number;
  max: number;
  std: number;
}

export interface WeatherClassifications {
  precipitation_source: string;
  rain_probability: number;
  very_hot_temp_percentile: number;
  very_snowy_probability: number;
  very_hot_feels_like_percentile: number;
  very_windy_percentile: number;
  very_wet_probability: number;
  very_wet_precip_threshold: number;
  very_wet_wind_threshold: number;
}

export interface WeatherMeta {
  latitude: number;
  longitude: number;
  center_datetime_utc: string;
  center_datetime_local: string;
  target_timezone: string;
  granularity: string;
  historical_data_range: [string, string];
}

export interface WeatherAnalyzeResponse {
  meta: WeatherMeta;
  stats: {
    [key: string]: WeatherStats;
  };
  classifications: WeatherClassifications;
  results: WeatherResult[];
}
