import React, { useEffect, useState } from 'react';
import { ChennaiMap } from '../components/ChennaiMap';
import { fetchStations, fetchPredictionMap, fetchHotspots, fetchPointPrediction, fetchPointExplanation } from '../services/api';
import type { StationInfo, PredictionPoint, HotspotInfo, LocalExplanationResponse } from '../types/api';
import { Layers, Eye, EyeOff, MapPin, Shield, Cpu } from 'lucide-react';

export const InteractiveMapPage: React.FC = () => {
  const [stations, setStations] = useState<StationInfo[]>([]);
  const [gridPoints, setGridPoints] = useState<PredictionPoint[]>([]);
  const [hotspots, setHotspots] = useState<HotspotInfo[]>([]);
  const [resolution, setResolution] = useState<number>(20);
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [showHotspots, setShowHotspots] = useState<boolean>(true);
  const [showStations, setShowStations] = useState<boolean>(true);
  
  const [selectedLocation, setSelectedLocation] = useState<{ latitude: number; longitude: number } | null>(null);
  const [selectedPrediction, setSelectedPrediction] = useState<PredictionPoint | null>(null);
  const [selectedExplanation, setSelectedExplanation] = useState<LocalExplanationResponse | null>(null);
  const [inspectLoading, setInspectLoading] = useState<boolean>(false);

  const loadMapData = async () => {
    try {
      const [stData, mapData, hsData] = await Promise.all([
        fetchStations(),
        fetchPredictionMap(resolution),
        fetchHotspots()
      ]);
      setStations(stData);
      setGridPoints(mapData.grid);
      setHotspots(hsData);
    } catch (err) {
      console.error('Failed to load map page data', err);
    }
  };

  useEffect(() => {
    loadMapData();
  }, [resolution]);

  const handleMapClick = async (lat: number, lon: number) => {
    setSelectedLocation({ latitude: lat, longitude: lon });
    setInspectLoading(true);
    try {
      const [pred, exp] = await Promise.all([
        fetchPointPrediction(lat, lon),
        fetchPointExplanation(lat, lon)
      ]);
      setSelectedPrediction(pred);
      setSelectedExplanation(exp);
    } catch (err) {
      console.error('Failed to fetch point inspection', err);
    } finally {
      setInspectLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-3xl shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Chennai Interactive Spatial Grid Map</h3>
            <p className="text-xs text-slate-400">Click anywhere on the map to trigger location inference & XAI explanation.</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
              showGrid
                ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/40'
                : 'bg-slate-950 text-slate-500 border-slate-800'
            }`}
          >
            {showGrid ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
            <span>Spatial Grid</span>
          </button>

          <button
            onClick={() => setShowHotspots(!showHotspots)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
              showHotspots
                ? 'bg-red-500/20 text-red-300 border-red-500/40'
                : 'bg-slate-950 text-slate-500 border-slate-800'
            }`}
          >
            {showHotspots ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
            <span>Hotspots</span>
          </button>

          <button
            onClick={() => setShowStations(!showStations)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
              showStations
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : 'bg-slate-950 text-slate-500 border-slate-800'
            }`}
          >
            {showStations ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
            <span>Ground Stations</span>
          </button>

          <div className="flex items-center space-x-2 bg-slate-950 border border-slate-800 px-3 py-1 rounded-xl text-xs">
            <span className="text-slate-400 font-medium">Grid Resolution:</span>
            <select
              value={resolution}
              onChange={(e) => setResolution(Number(e.target.value))}
              className="bg-transparent text-white font-bold focus:outline-none"
            >
              <option value={15} className="bg-slate-900">15 x 15 (Fast)</option>
              <option value={20} className="bg-slate-900">20 x 20 (Balanced)</option>
              <option value={25} className="bg-slate-900">25 x 25 (Detailed)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[640px]">
        <div className="lg:col-span-2 h-full">
          <ChennaiMap
            stations={showStations ? stations : []}
            gridPoints={showGrid ? gridPoints : []}
            hotspots={showHotspots ? hotspots : []}
            showGrid={showGrid}
            showHotspots={showHotspots}
            onMapClick={handleMapClick}
            selectedLocation={selectedLocation}
          />
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-xl flex flex-col justify-between overflow-y-auto">
          <div>
            <div className="flex items-center space-x-2 pb-3 border-b border-slate-800 mb-4">
              <MapPin className="w-5 h-5 text-sky-400" />
              <h3 className="text-base font-extrabold text-white">Location Inspector</h3>
            </div>

            {!selectedLocation ? (
              <div className="text-center py-16 space-y-3">
                <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-slate-500">
                  <MapPin className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-bold text-slate-300">No Location Selected</h4>
                <p className="text-xs text-slate-500 max-w-xs mx-auto">
                  Click on any point across the map of Chennai to inspect predicted pollution values, confidence intervals, and SHAP drivers.
                </p>
              </div>
            ) : inspectLoading ? (
              <div className="text-center py-16 space-y-3">
                <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                <p className="text-xs text-indigo-400 font-semibold">Running Spatial Ensemble Inference & XAI...</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-slate-950 p-3.5 rounded-2xl border border-slate-800">
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Coordinates</span>
                  <div className="text-xs font-mono font-bold text-slate-200 mt-0.5">
                    Lat: {selectedLocation.latitude.toFixed(4)} N, Lon: {selectedLocation.longitude.toFixed(4)} E
                  </div>
                </div>

                {selectedPrediction && (
                  <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-400">Predicted Air Quality</span>
                      <span
                        className="px-2.5 py-0.5 rounded-full text-xs font-extrabold"
                        style={{ backgroundColor: `${selectedPrediction.color}20`, color: selectedPrediction.color }}
                      >
                        {selectedPrediction.category}
                      </span>
                    </div>

                    <div className="text-3xl font-black" style={{ color: selectedPrediction.color }}>
                      {selectedPrediction.predicted_aqi} <span className="text-sm font-normal text-slate-400">AQI</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-slate-900 p-2 rounded-xl">
                        <span className="text-slate-500 text-[10px] block">PM2.5 Level</span>
                        <span className="font-bold text-slate-200">{selectedPrediction.predicted_pm25} µg/m³</span>
                      </div>
                      <div className="bg-slate-900 p-2 rounded-xl">
                        <span className="text-slate-500 text-[10px] block">PM10 Level</span>
                        <span className="font-bold text-slate-200">{selectedPrediction.predicted_pm10} µg/m³</span>
                      </div>
                    </div>

                    <div className="bg-slate-900/60 p-2.5 rounded-xl border border-slate-800 text-[11px] text-slate-400 space-y-1">
                      <div className="flex items-center justify-between">
                        <span>Model Uncertainty:</span>
                        <span className="font-bold text-indigo-400">{selectedPrediction.confidence_level}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>95% Prediction Interval:</span>
                        <span className="font-mono font-bold text-slate-300">
                          [{selectedPrediction.lower_bound_pm25} - {selectedPrediction.upper_bound_pm25}] µg/m³
                        </span>
                      </div>
                    </div>
                  </div>
                )}

                {selectedExplanation && (
                  <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-3">
                    <div className="flex items-center space-x-2 text-indigo-400 text-xs font-bold">
                      <Cpu className="w-4 h-4" />
                      <span>Key Predictive Drivers</span>
                    </div>

                    <div className="space-y-2 text-xs">
                      {selectedExplanation.positive_contributors.slice(0, 2).map((item, idx) => (
                        <div key={`pos-${idx}`} className="flex items-center justify-between bg-red-500/10 p-2 rounded-xl border border-red-500/20">
                          <span className="text-red-300 font-medium">{item.name}</span>
                          <span className="font-bold text-red-400">+{item.impact} µg/m³</span>
                        </div>
                      ))}
                      {selectedExplanation.negative_contributors.slice(0, 2).map((item, idx) => (
                        <div key={`neg-${idx}`} className="flex items-center justify-between bg-emerald-500/10 p-2 rounded-xl border border-emerald-500/20">
                          <span className="text-emerald-300 font-medium">{item.name}</span>
                          <span className="font-bold text-emerald-400">{item.impact} µg/m³</span>
                        </div>
                      ))}
                    </div>

                    <p className="text-[11px] text-slate-400 leading-relaxed italic bg-slate-900 p-2.5 rounded-xl border border-slate-800">
                      "{selectedExplanation.narrative}"
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-slate-800 text-[10px] text-slate-500 flex items-center justify-between">
            <span>CPCB Sub-Index Engine Active</span>
            <Shield className="w-3.5 h-3.5 text-indigo-400" />
          </div>
        </div>
      </div>
    </div>
  );
};
