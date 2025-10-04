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
  window_days?: number;
  baseline_start?: number;
  baseline_end?: number;
  detail?: string;
  units?: string;
}
