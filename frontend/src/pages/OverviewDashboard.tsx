import React, { useEffect, useState } from 'react';
import { KPICard } from '../components/KPICard';
import { ScientificAlert } from '../components/ScientificAlert';
import { ChennaiMap } from '../components/ChennaiMap';
import { fetchOverview, fetchStations, fetchPredictionMap } from '../services/api';
import type { AirQualityOverview, StationInfo, PredictionPoint } from '../types/api';
import { RefreshCw, MapPin, Radio, Sparkles } from 'lucide-react';

interface OverviewDashboardProps {
  onNavigateMap: () => void;
}

export const OverviewDashboard: React.FC<OverviewDashboardProps> = ({ onNavigateMap }) => {
  const [overview, setOverview] = useState<AirQualityOverview | null>(null);
  const [stations, setStations] = useState<StationInfo[]>([]);
  const [gridPoints, setGridPoints] = useState<PredictionPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ovData, stData, mapData] = await Promise.all([
        fetchOverview(),
        fetchStations(),
        fetchPredictionMap(15)
      ]);
      setOverview(ovData);
      setStations(stData);
      setGridPoints(mapData.grid);
    } catch (err) {
      console.error('Failed to load overview dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl">
        <div>
          <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold tracking-wider uppercase">
            <Sparkles className="w-4 h-4" />
            <span>Hybrid Environmental AI Engine</span>
          </div>
          <h2 className="text-2xl font-extrabold text-white mt-1">
            Chennai Air Quality Status & Spatial Predictions
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Fused Sentinel-5P TROPOMI satellite tropospheric columns, Open-Meteo weather physics, and 7 ground monitoring stations.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center space-x-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-bold transition-all border border-slate-700 self-start md:self-auto"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      <ScientificAlert />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        <KPICard
          title="Citywide AQI"
          value={overview?.current_aqi ?? '--'}
          category={overview?.category}
          color={overview?.color}
          subtext={overview?.health_advisory}
          trend="Ensemble Derived"
        />
        <KPICard
          title="PM2.5 Level"
          value={overview?.pollutants["PM2.5"] ?? '--'}
          unit="µg/m³"
          color="#38BDF8"
          subtext="Fine particulate matter (Dominant driver)"
        />
        <KPICard
          title="PM10 Level"
          value={overview?.pollutants["PM10"] ?? '--'}
          unit="µg/m³"
          color="#818CF8"
          subtext="Coarse inhalable particles"
        />
        <KPICard
          title="NO2 Level"
          value={overview?.pollutants["NO2"] ?? '--'}
          unit="µg/m³"
          color="#F472B6"
          subtext="Nitrogen dioxide traffic/combustion"
        />
        <KPICard
          title="SO2 Level"
          value={overview?.pollutants["SO2"] ?? '--'}
          unit="µg/m³"
          color="#FBBF24"
          subtext="Sulfur dioxide industrial emissions"
        />
        <KPICard
          title="CO Level"
          value={overview?.pollutants["CO"] ?? '--'}
          unit="mg/m³"
          color="#34D399"
          subtext="Carbon monoxide vehicular proxy"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-xl flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <MapPin className="w-5 h-5 text-indigo-400" />
              <h3 className="text-base font-bold text-white">Spatial Prediction Heatmap Quickview</h3>
            </div>
            <button
              onClick={onNavigateMap}
              className="text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              Open Full Interactive Map &rarr;
            </button>
          </div>

          <div className="flex-1 min-h-[380px] relative">
            <ChennaiMap stations={stations} gridPoints={gridPoints} showGrid={true} />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-xl flex flex-col">
          <div className="flex items-center space-x-2 mb-4">
            <Radio className="w-5 h-5 text-emerald-400" />
            <h3 className="text-base font-bold text-white">Active Ground Stations</h3>
          </div>

          <div className="space-y-3 overflow-y-auto max-h-[380px] pr-1">
            {stations.map((st) => (
              <div
                key={st.id}
                className="bg-slate-950/60 border border-slate-800/80 p-3.5 rounded-2xl flex items-center justify-between hover:border-slate-700 transition-all"
              >
                <div>
                  <h4 className="text-xs font-bold text-slate-200">{st.name}</h4>
                  <p className="text-[11px] text-slate-500">{st.zone_type}</p>
                  <span className="text-[10px] font-semibold text-slate-400">
                    PM2.5: {st.current_pm25} µg/m³
                  </span>
                </div>

                <div className="text-right">
                  <span
                    className="inline-block px-2.5 py-1 rounded-full text-xs font-extrabold shadow-sm"
                    style={{ backgroundColor: `${st.color}20`, color: st.color, border: `1px solid ${st.color}40` }}
                  >
                    {st.current_aqi} AQI
                  </span>
                  <span className="block text-[10px] text-slate-400 font-medium mt-0.5">
                    {st.category}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
