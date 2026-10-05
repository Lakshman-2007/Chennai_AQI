import React, { useEffect, useState } from 'react';
import { fetchHistoricalTrends, fetchStations } from '../services/api';
import type { StationInfo } from '../types/api';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, LineChart, Line } from 'recharts';
import { LineChart as LineIcon } from 'lucide-react';

export const TrendAnalyticsPage: React.FC = () => {
  const [days, setDays] = useState<number>(30);
  const [selectedStation, setSelectedStation] = useState<string>('all_stations_avg');
  const [stations, setStations] = useState<StationInfo[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [stData, histData] = await Promise.all([
        fetchStations(),
        fetchHistoricalTrends(days, selectedStation === 'all_stations_avg' ? undefined : selectedStation)
      ]);
      setStations(stData);
      setHistory(histData.history);
    } catch (err) {
      console.error('Failed to load trends data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [days, selectedStation]);

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <LineIcon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Historical Trends & Meteorological Correlations</h3>
            <p className="text-xs text-slate-400">Time-series analytics across ground pollutants, Sentinel-5P satellite passes, and weather dynamics.</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs">
          <div className="flex items-center space-x-2 bg-slate-950 border border-slate-800 px-3 py-1.5 rounded-xl">
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

          <div className="flex items-center space-x-1 bg-slate-950 border border-slate-800 p-1 rounded-xl">
            {[7, 30, 90, 180].map((d) => (
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
        </div>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-base font-extrabold text-white">Predicted AQI & PM2.5 Ground Concentration Trajectory</h4>
            <p className="text-xs text-slate-400">Daily average values over the selected {days}-day period</p>
          </div>
          <div className="flex items-center space-x-4 text-xs font-semibold">
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-indigo-500"></span>
              <span className="text-slate-300">Predicted AQI</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-sky-400"></span>
              <span className="text-slate-300">PM2.5 (µg/m³)</span>
            </div>
          </div>
        </div>

        <div className="h-[320px] w-full">
          {loading ? (
            <div className="h-full flex items-center justify-center text-xs text-indigo-400">
              Loading historical time-series data...
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="aqiGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="pm25Grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38BDF8" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#38BDF8" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="timestamp" stroke="#64748B" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748B" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '12px', fontSize: '12px' }}
                />
                <Area type="monotone" dataKey="aqi" stroke="#6366F1" strokeWidth={2} fillOpacity={1} fill="url(#aqiGrad)" name="AQI" />
                <Area type="monotone" dataKey="pm25" stroke="#38BDF8" strokeWidth={2} fillOpacity={1} fill="url(#pm25Grad)" name="PM2.5 (µg/m³)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-xl space-y-3">
          <h4 className="text-sm font-bold text-white">Multi-Pollutant Concentration Trends</h4>
          <div className="h-[240px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="timestamp" stroke="#64748B" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748B" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '12px', fontSize: '11px' }} />
                <Line type="monotone" dataKey="pm10" stroke="#818CF8" strokeWidth={2} dot={false} name="PM10" />
                <Line type="monotone" dataKey="no2" stroke="#F472B6" strokeWidth={2} dot={false} name="NO2" />
                <Line type="monotone" dataKey="so2" stroke="#FBBF24" strokeWidth={2} dot={false} name="SO2" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-xl space-y-3">
          <h4 className="text-sm font-bold text-white">Meteorological Factors (Wind & Humidity vs PM2.5)</h4>
          <div className="h-[240px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={history} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                <XAxis dataKey="timestamp" stroke="#64748B" tick={{ fontSize: 10 }} />
                <YAxis yAxisId="left" stroke="#64748B" tick={{ fontSize: 10 }} />
                <YAxis yAxisId="right" orientation="right" stroke="#64748B" tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '12px', fontSize: '11px' }} />
                <Line yAxisId="left" type="monotone" dataKey="pm25" stroke="#38BDF8" strokeWidth={2} dot={false} name="PM2.5" />
                <Line yAxisId="right" type="monotone" dataKey="wind_speed" stroke="#34D399" strokeWidth={1.5} dot={false} name="Wind Speed (km/h)" />
                <Line yAxisId="right" type="monotone" dataKey="humidity" stroke="#A78BFA" strokeWidth={1.5} dot={false} name="Humidity (%)" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
