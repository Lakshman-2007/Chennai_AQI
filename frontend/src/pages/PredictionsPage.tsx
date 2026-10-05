import React, { useEffect, useState } from 'react';
import { fetchHotspots, fetchPointPrediction } from '../services/api';
import type { HotspotInfo, PredictionPoint } from '../types/api';
import { Layers, AlertTriangle, Search } from 'lucide-react';

export const PredictionsPage: React.FC = () => {
  const [hotspots, setHotspots] = useState<HotspotInfo[]>([]);
  const [threshold, setThreshold] = useState<number>(55.0);
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
      const res = await fetchPointPrediction(lat, lon);
      setCustomPrediction(res);
    } catch (err) {
      console.error('Failed point prediction', err);
    } finally {
      setPredicting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Spatial Predictions & Hotspot Clustering Engine</h3>
            <p className="text-xs text-slate-400">Automated DBSCAN spatial clustering and point-wise ensemble inference with confidence bounds.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
            <Search className="w-5 h-5 text-indigo-400" />
            <h4 className="text-sm font-bold text-white">Custom Coordinate Query</h4>
          </div>

          <form onSubmit={handleCustomPredict} className="space-y-3">
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
              {predicting ? 'Running Ensemble Model...' : 'Query Location Prediction'}
            </button>
          </form>

          {customPrediction && (
            <div className="mt-4 bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-400">Prediction Result</span>
                <span
                  className="px-2.5 py-0.5 rounded-full text-xs font-extrabold"
                  style={{ backgroundColor: `${customPrediction.color}20`, color: customPrediction.color }}
                >
                  {customPrediction.category}
                </span>
              </div>

              <div className="text-3xl font-black" style={{ color: customPrediction.color }}>
                {customPrediction.predicted_aqi} <span className="text-xs text-slate-400">AQI</span>
              </div>

              <div className="text-xs space-y-1 text-slate-300">
                <div className="flex justify-between">
                  <span>PM2.5:</span>
                  <span className="font-bold">{customPrediction.predicted_pm25} µg/m³</span>
                </div>
                <div className="flex justify-between">
                  <span>PM10:</span>
                  <span className="font-bold">{customPrediction.predicted_pm10} µg/m³</span>
                </div>
                <div className="flex justify-between text-indigo-400">
                  <span>95% Confidence Interval:</span>
                  <span className="font-mono font-bold">[{customPrediction.lower_bound_pm25} - {customPrediction.upper_bound_pm25}]</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              <h4 className="text-sm font-bold text-white">Detected Pollution Hotspots in Chennai</h4>
            </div>

            <div className="flex items-center space-x-2 text-xs">
              <span className="text-slate-400">Threshold PM2.5:</span>
              <select
                value={threshold}
                onChange={(e) => setThreshold(Number(e.target.value))}
                className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1 text-white font-bold focus:outline-none"
              >
                <option value={45}>45 µg/m³ (Sensitive)</option>
                <option value={55}>55 µg/m³ (Moderate)</option>
                <option value={70}>70 µg/m³ (Severe)</option>
              </select>
            </div>
          </div>

          {loading ? (
            <div className="py-16 text-center text-xs text-indigo-400 font-semibold">
              Running spatial clustering algorithm...
            </div>
          ) : hotspots.length === 0 ? (
            <div className="py-16 text-center text-xs text-slate-500 font-medium">
              No pollution hotspots detected above the selected threshold of {threshold} µg/m³.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {hotspots.map((hs) => (
                <div
                  key={hs.hotspot_id}
                  className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-3 hover:border-slate-700 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-red-400 uppercase tracking-wide">
                      {hs.hotspot_id}
                    </span>
                    <span
                      className="px-2.5 py-0.5 rounded-full text-xs font-extrabold"
                      style={{ backgroundColor: `${hs.color}20`, color: hs.color }}
                    >
                      {hs.category}
                    </span>
                  </div>

                  <h5 className="text-sm font-extrabold text-white">{hs.location_name}</h5>

                  <div className="text-xs text-slate-400 space-y-1">
                    <div className="flex justify-between">
                      <span>Mean Predicted AQI:</span>
                      <span className="font-bold text-slate-200">{hs.mean_predicted_aqi}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Peak PM2.5 Level:</span>
                      <span className="font-bold text-red-400">{hs.peak_pm25} µg/m³</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Dominant Driver:</span>
                      <span className="font-bold text-indigo-400">{hs.dominant_pollutant}</span>
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-500 italic bg-slate-900/60 p-2 rounded-xl">
                    "{hs.advisory}"
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
