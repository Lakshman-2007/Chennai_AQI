import React, { useEffect, useState } from 'react';
import { KPICard } from '../components/KPICard';
import { ScientificAlert } from '../components/ScientificAlert';
import { ChennaiMap } from '../components/ChennaiMap';
import { fetchOverview, fetchStations, fetchPredictionMap } from '../services/api';
import type { AirQualityOverview, StationInfo, PredictionPoint } from '../types/api';
import { RefreshCw, MapPin, Radio, Sparkles, AlertCircle, Clock, ShieldCheck } from 'lucide-react';

interface OverviewDashboardProps {
  onNavigateMap: () => void;
}

export const OverviewDashboard: React.FC<OverviewDashboardProps> = ({ onNavigateMap }) => {
  const [overview, setOverview] = useState<AirQualityOverview | null>(null);
  const [stations, setStations] = useState<StationInfo[]>([]);
  const [gridPoints, setGridPoints] = useState<PredictionPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [mapView, setMapView] = useState<'interactive' | 'ward-snapshot'>('interactive');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovData, stData, mapData] = await Promise.all([
        fetchOverview(),
        fetchStations(),
        fetchPredictionMap(15, '+24h')
      ]);
      setOverview(ovData);
      setStations(stData);
      setGridPoints(mapData.grid);
    } catch (err: any) {
      console.error('Failed to load overview dashboard data', err);
      setError('Unable to load current overview data. Please verify backend server status.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner & Control */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl">
        <div>
          <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold tracking-wider uppercase">
            <Sparkles className="w-4 h-4" />
            <span>Chennai Environmental Intelligence Platform</span>
          </div>
          <h2 className="text-2xl font-extrabold text-white mt-1">
            Official CPCB AQI & Multi-Source Analytics
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            Ground air monitoring stations, Open-Meteo atmospheric covariates, Sentinel-5P satellite context, and walk-forward ensemble ML.
          </p>
        </div>

        <div className="flex items-center space-x-3 self-start md:self-auto">
          {overview && (
            <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300">
              <Clock className="w-3.5 h-3.5 text-indigo-400" />
              <span>Observed: {overview.last_updated ? new Date(overview.last_updated).toLocaleDateString() : 'N/A'}</span>
            </div>
          )}
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-indigo-600/20"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Scientific & Provenance Alert Banner */}
      <ScientificAlert
        dataMode={overview?.data_mode ?? 'demo'}
        freshness={overview?.freshness ?? 'stale'}
        showSatelliteNote={true}
      />

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-950/40 border border-red-500/30 rounded-2xl flex items-center justify-between text-xs text-red-300">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span>{error}</span>
          </div>
          <button
            onClick={loadData}
            className="px-3 py-1 bg-red-600/30 hover:bg-red-600 text-white rounded-lg font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* Primary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
        <KPICard
          title="Citywide AQI"
          value={overview?.current_aqi !== null && overview?.current_aqi !== undefined ? overview.current_aqi : '--'}
          category={overview?.category}
          color={overview?.color}
          subtext={overview?.health_advisory}
          trend={overview?.eligible ? `Dominant: ${overview.dominant_pollutant ?? 'PM2.5'}` : 'Insufficient Data'}
        />
        <KPICard
          title="PM2.5 Concentration"
          value={overview?.pollutants["PM2.5"] ?? '--'}
          unit="µg/m³"
          color="#38BDF8"
          subtext="Fine particulate matter"
        />
        <KPICard
          title="PM10 Concentration"
          value={overview?.pollutants["PM10"] ?? '--'}
          unit="µg/m³"
          color="#818CF8"
          subtext="Inhalable particulate matter"
        />
        <KPICard
          title="NO2 Concentration"
          value={overview?.pollutants["NO2"] ?? '--'}
          unit="µg/m³"
          color="#F472B6"
          subtext="Nitrogen dioxide (Traffic / Combustion)"
        />
        <KPICard
          title="SO2 Concentration"
          value={overview?.pollutants["SO2"] ?? '--'}
          unit="µg/m³"
          color="#FBBF24"
          subtext="Sulfur dioxide (Industrial sources)"
        />
        <KPICard
          title="Active Monitors"
          value={overview?.total_active_stations ?? '--'}
          color="#34D399"
          subtext="CPCB CAAQMS Stations in Chennai"
          trend="100% Reporting"
        />
      </div>

      {/* Sub-indices Breakdown & Station Status Row */}
      {overview && overview.sub_indices && Object.keys(overview.sub_indices).length > 0 && (
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Official CPCB Pollutant Sub-Indices Breakdown</span>
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">
              Formula: CPCB NAQI (2014-2015 Technical Standard)
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
            {Object.entries(overview.sub_indices).map(([pol, si]) => (
              <div key={pol} className="p-3 bg-slate-950 rounded-2xl border border-slate-800 flex flex-col justify-between">
                <span className="text-xs text-slate-400 font-semibold">{pol} Sub-Index</span>
                <span className="text-xl font-black text-white mt-1">
                  {si} <span className="text-xs font-normal text-slate-400">/ 500</span>
                </span>
                <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-indigo-500"
                    style={{ width: `${Math.min(100, (si / 300) * 100)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Map Preview & Station List Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map Preview Container */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl flex flex-col">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div className="flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-indigo-400" />
              <h3 className="text-base font-bold text-white">Live Chennai Monitoring Map Preview</h3>
            </div>
            <button
              onClick={onNavigateMap}
              className="text-xs font-bold text-indigo-400 hover:text-indigo-300 underline"
            >
              Open Full Interactive Map →
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-2 mb-3" role="group" aria-label="Map preview mode">
            <button
              type="button"
              onClick={() => setMapView('interactive')}
              aria-pressed={mapView === 'interactive'}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${mapView === 'interactive' ? 'bg-indigo-600 border-indigo-500 text-white' : 'bg-slate-950 border-slate-700 text-slate-300 hover:border-indigo-500'}`}
            >
              Interactive map
            </button>
            <button
              type="button"
              onClick={() => setMapView('ward-snapshot')}
              aria-pressed={mapView === 'ward-snapshot'}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${mapView === 'ward-snapshot' ? 'bg-indigo-600 border-indigo-500 text-white' : 'bg-slate-950 border-slate-700 text-slate-300 hover:border-indigo-500'}`}
            >
              Ward-level AQI snapshot
            </button>
          </div>

          <div className="h-[360px] w-full rounded-2xl overflow-hidden border border-slate-800 bg-slate-950">
            {mapView === 'interactive' ? (
              <ChennaiMap
                stations={stations}
                gridPoints={gridPoints}
                showHotspots={false}
                showWards={true}
                compact={true}
              />
            ) : (
              <div className="h-full w-full flex flex-col">
                <img
                  src="/images/chennai-ward-aqi-snapshot.png"
                  alt="Chennai ward-level AQI interpolation snapshot with latitude and longitude axes"
                  className="w-full h-full object-contain"
                  loading="lazy"
                />
                <p className="px-3 py-2 text-[11px] text-amber-200 bg-slate-900 border-t border-slate-800">
                  Reference snapshot supplied for the project; its displayed station values are not a live feed. Map extent is approximately 12.85–13.23° N and 80.14–80.33° E.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Station Readout Panel */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Radio className="w-4 h-4 text-emerald-400" />
                <h3 className="text-base font-bold text-white">Ground Stations</h3>
              </div>
              <span className="text-xs text-slate-400 font-semibold">{stations.length} Active</span>
            </div>

            <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
              {stations.map((st) => (
                <div
                  key={st.id}
                  className="p-3 bg-slate-950 rounded-2xl border border-slate-800 flex items-center justify-between hover:border-slate-700 transition-all"
                >
                  <div>
                    <div className="text-xs font-bold text-white">{st.name}</div>
                    <div className="text-[10px] text-slate-400">{st.zone_type}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-extrabold" style={{ color: st.color }}>
                      {st.current_aqi !== null ? `${st.current_aqi} AQI` : 'Ineligible'}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      PM2.5: {st.current_pm25} µg/m³
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={onNavigateMap}
            className="w-full mt-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl transition-all border border-slate-700"
          >
            Inspect Localized Air Quality
          </button>
        </div>
      </div>
    </div>
  );
};
