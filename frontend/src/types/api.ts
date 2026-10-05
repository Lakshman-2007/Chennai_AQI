export interface AirQualityOverview {
  current_aqi: number;
  category: string;
  color: string;
  health_advisory: string;
  dominant_pollutant: string;
  last_updated: string;
  pollutants: Record<string, number>;
  total_active_stations: number;
}

export interface StationInfo {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  zone_type: string;
  current_pm25: number;
  current_aqi: number;
  category: string;
  color: string;
}

export interface StationDetails extends StationInfo {
  aqi_summary: {
    aqi: number;
    category: string;
    color: string;
    health_advisory: string;
    dominant_pollutant: string;
    sub_indices: Record<string, number>;
  };
  satellite_features: {
    satellite_no2: number;
    satellite_so2: number;
    satellite_co: number;
    satellite_o3: number;
    aerosol_index: number;
  };
  meteorological_conditions: {
    temperature: number;
    humidity: number;
    wind_speed: number;
    wind_direction: number;
    pressure: number;
    boundary_layer_height: number;
  };
  last_updated: string;
}

export interface PredictionPoint {
  latitude: number;
  longitude: number;
  predicted_pm25: number;
  predicted_pm10: number;
  predicted_no2: number;
  predicted_so2: number;
  predicted_aqi: number;
  category: string;
  color: string;
  confidence_level: string;
  uncertainty_pm25: number;
  lower_bound_pm25: number;
  upper_bound_pm25: number;
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
  timestamp: string;
}

export interface HotspotInfo {
  hotspot_id: string;
  location_name: string;
  center_latitude: number;
  center_longitude: number;
  peak_pm25: number;
  mean_predicted_aqi: number;
  category: string;
  color: string;
  dominant_pollutant: string;
  cell_count: number;
  confidence: string;
  advisory: string;
}

export interface FeatureImpact {
  feature: string;
  name: string;
  impact: number;
  raw_value: number;
}

export interface LocalExplanationResponse {
  location: {
    latitude: number;
    longitude: number;
  };
  predicted_pm25: number;
  predicted_aqi: number;
  base_value: number;
  positive_contributors: FeatureImpact[];
  negative_contributors: FeatureImpact[];
  narrative: string;
}

export interface ModelMetric {
  model: string;
  r2: number;
  rmse: number;
  mae: number;
  mape: number;
}

export interface ModelPerformanceResponse {
  best_model: string;
  best_r2: number;
  best_rmse: number;
  best_mae: number;
  comparison: ModelMetric[];
  ensemble_weights: Record<string, number>;
  metadata: {
    target_variable: string;
    num_train_samples: number;
    num_test_samples: number;
    stations_count: number;
    time_range: {
      start: string;
      end: string;
    };
  };
}

export interface DataSourceInfo {
  name: string;
  type: string;
  provider: string;
  description: string;
  variables: string[];
  access_method: string;
  status: string;
}

export interface DataQualityReport {
  total_records: number;
  total_stations: number;
  time_range: {
    start: string;
    end: string;
  };
  missing_data_percentage: number;
  completeness_score: number;
  data_alignment_method: string;
  scientific_integrity_verified: boolean;
}
