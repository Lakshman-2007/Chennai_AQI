import React, { useEffect, useState } from 'react';
import { fetchHotspots, fetchPointPrediction } from '../services/api';
import type { HotspotInfo, PredictionPoint } from '../types/api';
import { Layers, Search, Clock } from 'lucide-react';
import { ScientificAlert } from '../components/ScientificAlert';

export const PredictionsPage: React.FC = () => {
  const [hotspots, setHotspots] = useState<HotspotInfo[]>([]);
  const [threshold, setThreshold] = useState<number>(55.0);
  const [horizon, setHorizon] = useState<string>('+24h');
  const [loading, setLoading] = useState<boolean>(true);

  const [latInput, setLatInput] = useState<string>('13.0827');
  const [lonInput, setLonInput] = useState<string>('80.2707');
  const [customPrediction, setCustomPrediction] = useState<PredictionPoint | null>(null);
  const [predicting, setPredicting] = useState<boolean>(false);

  const loadHotspots = async () => {
    setLoading(true);
    try {
      const data = await fetchHotspots(threshold);
      setHotspots(data);
    } catch (err) {
      console.error('Failed to load hotspots', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHotspots();
  }, [threshold]);

  const handleCustomPredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setPredicting(true);
    try {
      const lat = parseFloat(latInput);
      const lon = parseFloat(lonInput);
      const res = await fetchPointPrediction(lat, lon, horizon);
      setCustomPrediction(res);
    } catch (err) {
      console.error('Failed point prediction', err);
    } finally {
      setPredicting(false);
    }
  };

  return (
    <div className="space-y-6">
      <ScientificAlert showSatelliteNote={false} />

      {/* Header Bar */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Prospective Forecasting & Hotspot Spatial Clustering</h3>
            <p className="text-xs text-slate-400">
              PM2.5 concentration forecast with calibrated 95% uncertainty intervals and DBSCAN cluster detection.
            </p>
          </div>
        </div>

        {/* Global Horizon Selector */}
        <div className="flex items-center space-x-1 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 text-xs">
          <Clock className="w-4 h-4 text-indigo-400 ml-1.5" />
          <span className="text-slate-400 font-semibold px-1">Valid Horizon:</span>
          {['+1h', '+6h', '+12h', '+24h'].map((h) => (
            <button
              key={h}
              onClick={() => setHorizon(h)}
              className={`px-3 py-1 rounded-xl font-bold transition-all ${
                horizon === h
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {h}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Custom Point Query Panel */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
            <Search className="w-4 h-4 text-indigo-400" />
            <h4 className="text-sm font-bold text-white">Single-Coordinate Forecast</h4>
          </div>

          <form onSubmit={handleCustomPredict} className="space-y-3.5">
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Latitude (°N)</label>
              <input
                type="number"
                step="0.0001"
                min="12.75"
                max="13.25"
                value={latInput}
                onChange={(e) => setLatInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
                required
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1">Longitude (°E)</label>
              <input
                type="number"
                step="0.0001"
                min="80.05"
                max="80.35"
                value={lonInput}
                onChange={(e) => setLonInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
                required
              />
            </div>

            <button
              type="submit"
              disabled={predicting}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl text-xs transition-all shadow-lg shadow-indigo-600/20"
            >
              {predicting ? 'Evaluating Ensemble...' : `Compute Forecast (${horizon})`}
            </button>
          </form>

          {/* Point Prediction Output Card */}
          {customPrediction && (
            <div className="mt-4 p-4 bg-slate-950 rounded-2xl border border-slate-800 space-y-3 animate-fade-in">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400">
                  Target: {customPrediction.target} Forecast
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-900/40 text-indigo-300">
                  {customPrediction.horizon}
                </span>
              </div>

              <div>
                <div className="text-3xl font-black text-white">
                  {customPrediction.predicted_pm25}{' '}
                  <span className="text-xs font-semibold text-slate-400">{customPrediction.unit}</span>
                </div>
                <div className="flex items-center space-x-2 mt-1">
                  <span
                    className="text-xs font-bold px-2 py-0.5 rounded-full"
                    style={{ backgroundColor: `${customPrediction.color}25`, color: customPrediction.color }}
                  >
                    Derived AQI: ~{customPrediction.predicted_aqi} ({customPrediction.category})
                  </span>
                </div>
              </div>

              {/* 95% Confidence Interval */}
              <div className="p-2.5 bg-slate-900 rounded-xl text-xs space-y-1">
                <div className="text-[11px] text-slate-400 font-semibold">95% Calibrated Confidence Interval:</div>
                <div className="font-mono font-bold text-sky-400 text-xs">
                  [{customPrediction.lower_bound_pm25} — {customPrediction.upper_bound_pm25}] {customPrediction.unit}
                </div>
              </div>

              <div className="space-y-1 text-[10px] text-slate-400 border-t border-slate-800/80 pt-2 font-mono">
                <div>Issued: {new Date(customPrediction.issued_at).toLocaleTimeString()}</div>
                <div>Valid At: {new Date(customPrediction.valid_at).toLocaleString()}</div>
                <div>Model: {customPrediction.model_version}</div>
              </div>
            </div>
          )}
        </div>

        {/* Hotspot Clustering Panel */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
            <div>
              <h4 className="text-base font-bold text-white">Identified Spatial Pollution Hotspots</h4>
              <p className="text-xs text-slate-400">
                DBSCAN spatial density clusters identified with PM2.5 threshold: {threshold} µg/m³.
              </p>
            </div>

            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-400 font-semibold">Threshold:</span>
              <input
                type="range"
                min="40"
                max="80"
                step="5"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="accent-indigo-500 cursor-pointer"
              />
              <span className="font-mono font-bold text-indigo-400">{threshold} µg/m³</span>
            </div>
          </div>

          <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
            {loading ? (
              <div className="py-12 text-center text-xs text-indigo-400">Clustering spatial grid...</div>
            ) : hotspots.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-500">
                No persistent clusters above {threshold} µg/m³ threshold.
              </div>
            ) : (
              hotspots.map((hs) => (
                <div
                  key={hs.cluster_id}
                  className="p-4 bg-slate-950 rounded-2xl border border-slate-800 flex flex-wrap items-center justify-between gap-3 hover:border-slate-700 transition-all"
                >
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-white">Hotspot Cluster #{hs.cluster_id}</span>
                      <span
                        className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: `${hs.color}25`, color: hs.color }}
                      >
                        {hs.severity} Severity
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 mt-1">
                      Center: {hs.center_latitude}°N, {hs.center_longitude}°E ({hs.point_count} grid cells)
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-lg font-black" style={{ color: hs.color }}>
                      Mean PM2.5: {hs.mean_pm25} µg/m³
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Estimated AQI: ~{hs.estimated_aqi} ({hs.category})
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
