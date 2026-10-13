export interface AirQualityOverview {
  current_aqi: number | null;
  category: string;
  color: string;
  health_advisory: string;
  dominant_pollutant: string | null;
  last_updated: string | null;
  pollutants: Record<string, number | null>;
  sub_indices?: Record<string, number>;
  total_active_stations: number;
  data_mode: 'demo' | 'manual_import' | 'live';
  data_status: 'observed' | 'derived' | 'estimated' | 'forecast' | 'synthetic' | 'manual_import';
  freshness: 'fresh' | 'stale' | 'expired' | 'unavailable';
  age_seconds?: number | null;
  is_synthetic: boolean;
  eligible: boolean;
  eligibility_reason?: string | null;
}

export interface StationInfo {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  zone_type: string;
  current_pm25: number;
  current_aqi: number | null;
  category: string;
  color: string;
  dominant_pollutant?: string | null;
  last_updated?: string | null;
  freshness: 'fresh' | 'stale' | 'expired' | 'unavailable';
  age_seconds?: number | null;
  data_status: string;
}

export interface StationDetails extends StationInfo {
  aqi_summary: {
    aqi: number | null;
    category: string;
    color: string;
    health_advisory: string;
    dominant_pollutant: string | null;
    sub_indices: Record<string, number>;
    eligible: boolean;
  };
  pollutant_readings: Record<string, number>;
  satellite_context: {
    satellite_no2_column: number;
    satellite_so2_column: number;
    aerosol_index: number;
    note: string;
  };
  meteorological_conditions: {
    temperature: number;
    humidity: number;
    wind_speed: number;
    wind_direction: number;
    surface_pressure: number;
    boundary_layer_height: number;
  };
}

export interface PredictionPoint {
  latitude: number;
  longitude: number;
  target: string;
  unit: string;
  predicted_pm25: number;
  derived_pm25_sub_index?: number | null;
  predicted_aqi: number | null;
  category: string;
  color: string;
  lower_bound_pm25: number;
  upper_bound_pm25: number;
  disagreement_range_lower?: number;
  disagreement_range_upper?: number;
  ensemble_std?: number;
  confidence_level: string;
  uncertainty_label?: string;
  empirical_coverage_pct?: number | null;
  issued_at: string;
  valid_at: string;
  horizon: string;
  model_version: string;
  uncertainty_status: string;
  input_status?: string;
  weather_vintage_status?: string;
  aqi_caveat?: string;
  data_status: string;
}

export interface SpatialGridResponse {
  grid: PredictionPoint[];
  total_cells: number;
  bounds: {
    min_lat: number;
    max_lat: number;
    min_lon: number;
    max_lon: number;
  };
  issued_at: string;
  valid_at: string;
  horizon: string;
  model_version: string;
  target: string;
  unit: string;
  input_status?: string;
  weather_vintage_status?: string;
}

export interface HotspotInfo {
  cluster_id: number;
  center_latitude: number;
  center_longitude: number;
  mean_pm25: number;
  estimated_aqi: number;
  category: string;
  color: string;
  point_count: number;
  severity: string;
  method: string;
  layer_type?: string;
  source_time_range?: { start?: string; end?: string };
  spatial_reference?: string;
  data_mode?: string;
}

export interface FeatureImpact {
  feature: string;
  name: string;
  impact: number;
  raw_value: number;
}

export interface LocalExplanationResponse {
  base_value: number;
  prediction_pm25: number;
  target: string;
  unit: string;
  model_version: string;
  surrogate_model?: string;
  positive_contributors: FeatureImpact[];
  negative_contributors: FeatureImpact[];
  narrative: string;
  disclaimer: string;
}

export interface GlobalImportanceItem {
  feature: string;
  name: string;
  importance: number;
}

export interface ModelPerformanceItem {
  model: string;
  mae: number;
  rmse: number;
  r2: number;
  mape: number;
}

export interface ModelPerformanceResponse {
  best_model: string;
  best_r2: number;
  best_rmse: number;
  best_mae: number;
  comparison: ModelPerformanceItem[];
  ensemble_weights: Record<string, number>;
  metadata: Record<string, any>;
  model_card?: Record<string, any>;
}

export interface DataSourceInfo {
  name: string;
  type: string;
  provider: string;
  description: string;
  variables: string[];
  access_method: string;
  status: string;
  mode: string;
  freshness: string;
  attribution: string;
}

export interface LocalityItem {
  name: string;
  canonical_name: string;
  latitude: number;
  longitude: number;
  zone: string;
  type: string;
  has_ground_station: boolean;
  station_id?: string | null;
}

export interface ImportManifest {
  import_id: string;
  source_file: string;
  file_sha256: string;
  source_url_or_origin: string;
  downloaded_at: string;
  imported_at: string;
  total_rows_read: number;
  rows_accepted: number;
  rows_rejected: number;
  rejection_reasons: Record<string, number>;
  station_ids_found: string[];
  pollutants_found: string[];
  time_range_start?: string;
  time_range_end?: string;
  status: string;
}

export interface SourceHealthItem {
  source_id: string;
  name: string;
  provider: string;
  mode: string;
  status: string;
  last_attempt_at?: string;
  last_success_at?: string;
  age_seconds?: number;
  freshness: string;
  stale_threshold_hours: number;
  record_count: number;
  data_status: string;
  attribution: string;
  error_message?: string | null;
}
