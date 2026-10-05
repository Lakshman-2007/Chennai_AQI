import axios from 'axios';
import type {
  AirQualityOverview,
  StationInfo,
  StationDetails,
  SpatialGridResponse,
  PredictionPoint,
  HotspotInfo,
  LocalExplanationResponse,
  ModelPerformanceResponse,
  DataSourceInfo,
  DataQualityReport
} from '../types/api';

const API_BASE_URL = '/api';

export const fetchOverview = async (): Promise<AirQualityOverview> => {
  const res = await axios.get(`${API_BASE_URL}/overview`);
  return res.data;
};

export const fetchStations = async (): Promise<StationInfo[]> => {
  const res = await axios.get(`${API_BASE_URL}/stations`);
  return res.data;
};

export const fetchStationDetails = async (stationId: string): Promise<StationDetails> => {
  const res = await axios.get(`${API_BASE_URL}/stations/${stationId}`);
  return res.data;
};

export const fetchHistoricalTrends = async (days: number = 30, stationId?: string) => {
  const params: Record<string, any> = { days };
  if (stationId) params.station_id = stationId;
  const res = await axios.get(`${API_BASE_URL}/air-quality/history`, { params });
  return res.data;
};

export const fetchPredictionMap = async (resolution: number = 25, targetDate?: string): Promise<SpatialGridResponse> => {
  const params: Record<string, any> = { resolution };
  if (targetDate) params.target_date = targetDate;
  const res = await axios.get(`${API_BASE_URL}/predictions/map`, { params });
  return res.data;
};

export const fetchPointPrediction = async (lat: number, lon: number): Promise<PredictionPoint> => {
  const res = await axios.post(`${API_BASE_URL}/predictions/point`, {
    latitude: lat,
    longitude: lon
  });
  return res.data;
};

export const fetchHotspots = async (thresholdPm25: number = 60.0): Promise<HotspotInfo[]> => {
  const res = await axios.get(`${API_BASE_URL}/hotspots`, {
    params: { threshold_pm25: thresholdPm25 }
  });
  return res.data;
};

export const fetchGlobalExplanation = async () => {
  const res = await axios.get(`${API_BASE_URL}/explain/global`);
  return res.data;
};

export const fetchPointExplanation = async (lat: number, lon: number): Promise<LocalExplanationResponse> => {
  const res = await axios.post(`${API_BASE_URL}/explain/point`, {
    latitude: lat,
    longitude: lon
  });
  return res.data;
};

export const fetchModelPerformance = async (): Promise<ModelPerformanceResponse> => {
  const res = await axios.get(`${API_BASE_URL}/model/performance`);
  return res.data;
};

export const fetchDataSources = async (): Promise<DataSourceInfo[]> => {
  const res = await axios.get(`${API_BASE_URL}/data/sources`);
  return res.data;
};

export const fetchDataQuality = async (): Promise<DataQualityReport> => {
  const res = await axios.get(`${API_BASE_URL}/data/quality`);
  return res.data;
};
