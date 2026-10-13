import React, { useEffect, useState } from 'react';
import { fetchHistoricalTrends, fetchStations, exportDataUrl } from '../services/api';
import type { StationInfo } from '../types/api';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, LineChart, Line } from 'recharts';
import { LineChart as LineIcon, Download, Filter, Database, AlertCircle } from 'lucide-react';
import { ScientificAlert } from '../components/ScientificAlert';

export const TrendAnalyticsPage: React.FC = () => {
  const [days, setDays] = useState<number>(30);
  const [selectedStation, setSelectedStation] = useState<string>('all_stations_avg');
  const [stations, setStations] = useState<StationInfo[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [stData, histData] = await Promise.all([
        fetchStations(),
        fetchHistoricalTrends(days, selectedStation === 'all_stations_avg' ? undefined : selectedStation)
      ]);
      setStations(stData);
      setHistory(histData.history || []);
    } catch (err) {
      console.error('Failed to load trends data', err);
      setError('Failed to fetch historical trend series. Check backend service connectivity.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [days, selectedStation]);

  const handleExportCsv = () => {
    window.open(exportDataUrl('csv', days, selectedStation), '_blank');
  };

  const handleExportJson = () => {
    window.open(exportDataUrl('json', days, selectedStation), '_blank');
  };

  return (
    <div className="space-y-6">
      <ScientificAlert showSatelliteNote={false} />

      {/* Control & Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <LineIcon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Historical Trends & Meteorological Dynamics</h3>
            <p className="text-xs text-slate-400">
              Filter by monitoring station and analysis window. Total samples: {history.length} records.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          {/* Station Filter Dropdown */}
          <div className="flex items-center space-x-2 bg-slate-950 border border-slate-800 px-3 py-2 rounded-xl">
            <Filter className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400 font-semibold">Station:</span>
            <select
              value={selectedStation}
              onChange={(e) => setSelectedStation(e.target.value)}
              className="bg-transparent text-white font-bold focus:outline-none"
            >
              <option value="all_stations_avg" className="bg-slate-900">Citywide Average</option>
              {stations.map((st) => (
                <option key={st.id} value={st.id} className="bg-slate-900">{st.name}</option>
              ))}
            </select>
          </div>

          {/* Time Window Buttons */}
          <div className="flex items-center space-x-1 bg-slate-950 border border-slate-800 p-1 rounded-xl">
            {[7, 30, 90, 180, 365].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1 rounded-lg font-bold transition-all ${
                  days === d
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {d}D
              </button>
            ))}
          </div>

          {/* Export Actions (FR-23) */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleExportCsv}
              className="flex items-center space-x-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl font-bold border border-slate-700 transition-all"
            >
              <Download className="w-3.5 h-3.5 text-emerald-400" />
              <span>CSV Export</span>
            </button>
            <button
              onClick={handleExportJson}
              className="flex items-center space-x-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl font-bold border border-slate-700 transition-all"
            >
              <Database className="w-3.5 h-3.5 text-sky-400" />
              <span>JSON</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-500/30 rounded-2xl flex items-center justify-between text-xs text-red-300">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span>{error}</span>
          </div>
          <button onClick={loadData} className="px-3 py-1 bg-red-600/30 hover:bg-red-600 text-white rounded-lg font-semibold">
            Retry
          </button>
        </div>
      )}

      {/* Main PM2.5 & AQI Trajectory Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-base font-extrabold text-white">CPCB AQI & PM2.5 Ground Concentration Trajectory</h4>
            <p className="text-xs text-slate-400">Daily average readings over the selected {days}-day period</p>
          </div>
          <div className="flex items-center space-x-4 text-xs font-semibold">
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-indigo-500"></span>
              <span className="text-slate-300">CPCB AQI</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-sky-400"></span>
              <span className="text-slate-300">PM2.5 (µg/m³)</span>
            </div>
          </div>
        </div>

        <div className="h-[320px] w-full">
          {loading ? (
            <div className="h-full flex items-center justify-center text-xs text-indigo-400 animate-pulse">
              Loading time series analytics...
            </div>
          ) : history.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">
              No historical observations matching filter.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history}>
                <defs>
                  <linearGradient id="aqiGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="pm25Grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38BDF8" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#38BDF8" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="timestamp" stroke="#64748B" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="aqi" stroke="#6366F1" strokeWidth={2.5} fill="url(#aqiGrad)" name="CPCB AQI" />
                <Area type="monotone" dataKey="pm25" stroke="#38BDF8" strokeWidth={2} fill="url(#pm25Grad)" name="PM2.5 (µg/m³)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Multi-Pollutant & Weather Dual-Axis Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Co-Pollutants (PM10, NO2, SO2) */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
          <h4 className="text-sm font-bold text-white">Co-Pollutants Trend: PM10, NO2, SO2 (µg/m³)</h4>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="timestamp" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={10} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '10px', fontSize: '11px' }} />
                <Line type="monotone" dataKey="pm10" stroke="#A855F7" strokeWidth={2} dot={false} name="PM10" />
                <Line type="monotone" dataKey="no2" stroke="#EC4899" strokeWidth={2} dot={false} name="NO2" />
                <Line type="monotone" dataKey="so2" stroke="#F59E0B" strokeWidth={2} dot={false} name="SO2" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Meteorological Coupling (Temperature, Humidity, Wind Speed) */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
          <h4 className="text-sm font-bold text-white">Surface Meteorological Dynamics (Open-Meteo)</h4>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="timestamp" stroke="#64748B" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748B" fontSize={10} tickLine={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '10px', fontSize: '11px' }} />
                <Line type="monotone" dataKey="temperature" stroke="#EF4444" strokeWidth={2} dot={false} name="Temp (°C)" />
                <Line type="monotone" dataKey="humidity" stroke="#3B82F6" strokeWidth={2} dot={false} name="Humidity (%)" />
                <Line type="monotone" dataKey="wind_speed" stroke="#10B981" strokeWidth={2} dot={false} name="Wind Speed (km/h)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
