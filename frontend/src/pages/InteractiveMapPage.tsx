import React, { useEffect, useState } from 'react';
import { ChennaiMap } from '../components/ChennaiMap';
import { fetchStations, fetchPredictionMap, fetchHotspots, fetchPointPrediction, fetchPointExplanation } from '../services/api';
import type { StationInfo, PredictionPoint, HotspotInfo, LocalExplanationResponse } from '../types/api';
import { Layers, Eye, EyeOff, MapPin, Clock, AlertCircle } from 'lucide-react';
import { ScientificAlert } from '../components/ScientificAlert';

export const InteractiveMapPage: React.FC = () => {
  const [stations, setStations] = useState<StationInfo[]>([]);
  const [gridPoints, setGridPoints] = useState<PredictionPoint[]>([]);
  const [hotspots, setHotspots] = useState<HotspotInfo[]>([]);
  const [resolution, setResolution] = useState<number>(20);
  const [horizon, setHorizon] = useState<string>('+24h');
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [showHotspots, setShowHotspots] = useState<boolean>(true);
  const [showStations, setShowStations] = useState<boolean>(true);
  const [showWards, setShowWards] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedLocation, setSelectedLocation] = useState<{ latitude: number; longitude: number } | null>(null);
  const [selectedPrediction, setSelectedPrediction] = useState<PredictionPoint | null>(null);
  const [selectedExplanation, setSelectedExplanation] = useState<LocalExplanationResponse | null>(null);
  const [inspectLoading, setInspectLoading] = useState<boolean>(false);

  const loadMapData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [stData, mapData, hsData] = await Promise.all([
        fetchStations(),
        fetchPredictionMap(resolution, horizon),
        fetchHotspots(55.0, resolution)
      ]);
      setStations(stData);
      setGridPoints(mapData.grid);
      setHotspots(hsData);
    } catch (err: any) {
      console.error('Failed to load map page data', err);
      setError('Unable to load map layers from backend service. Check network or API readiness.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMapData();
  }, [resolution, horizon]);

  const handleMapClick = async (lat: number, lon: number) => {
    setSelectedLocation({ latitude: lat, longitude: lon });
    setInspectLoading(true);
    try {
      const [pred, exp] = await Promise.all([
        fetchPointPrediction(lat, lon, horizon),
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
      <ScientificAlert showSatelliteNote={false} />

      {/* Header & Controls Toolbar */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-3xl shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Chennai Multi-Layer Spatial Map</h3>
            <p className="text-xs text-slate-400">Search localities or click anywhere for instant localized ML prediction & SHAP attribution.</p>
          </div>
        </div>

        {/* Forecast Horizon Selector & Layer Toggles */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Horizon Selector */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <Clock className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
            <span className="text-[11px] text-slate-400 font-semibold px-1">Horizon:</span>
            {['+1h', '+6h', '+12h', '+24h'].map((h) => (
              <button
                key={h}
                onClick={() => setHorizon(h)}
                className={`px-2 py-1 rounded-lg text-xs font-bold transition-all ${
                  horizon === h
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {h}
              </button>
            ))}
          </div>

          {/* Grid Resolution Selector */}
          <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
            <span className="text-[11px] text-slate-400 font-semibold px-1">Grid:</span>
            {[15, 20, 25].map((res) => (
              <button
                key={res}
                onClick={() => setResolution(res)}
                className={`px-2 py-1 rounded-lg text-xs font-bold transition-all ${
                  resolution === res
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {res}x{res}
              </button>
            ))}
          </div>

          {loading && (
            <span className="text-[10px] text-indigo-400 animate-pulse font-mono px-1">
              Updating layers...
            </span>
          )}

          {/* Layer Toggles */}
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
            <span>Stations</span>
          </button>

          <button
            onClick={() => setShowWards(!showWards)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
              showWards
                ? 'bg-purple-500/20 text-purple-300 border-purple-500/40'
                : 'bg-slate-950 text-slate-500 border-slate-800'
            }`}
          >
            {showWards ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
            <span>GCC Wards</span>
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-950/40 border border-red-500/30 rounded-2xl p-4 flex items-center justify-between text-red-300 text-xs">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span>{error}</span>
          </div>
          <button
            onClick={loadMapData}
            className="px-3 py-1 bg-red-600/30 hover:bg-red-600 text-white rounded-lg font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* Main Map + Inspector Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 h-[620px]">
          <ChennaiMap
            stations={stations}
            gridPoints={gridPoints}
            hotspots={hotspots}
            showGrid={showGrid}
            showHotspots={showHotspots}
            showStations={showStations}
            showWards={showWards}
            onMapClick={handleMapClick}
            selectedLocation={selectedLocation}
          />
        </div>

        {/* Location Point Inspector Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-xl h-full flex flex-col justify-between">
            <div>
              <div className="flex items-center space-x-2 mb-3">
                <MapPin className="w-4 h-4 text-indigo-400" />
                <h4 className="text-sm font-bold text-white">Location Inspector</h4>
              </div>

              {!selectedLocation ? (
                <div className="text-center py-12 px-4 border border-dashed border-slate-800 rounded-2xl">
                  <div className="w-10 h-10 mx-auto rounded-xl bg-slate-800/80 flex items-center justify-center text-slate-400 mb-2">
                    <MapPin className="w-5 h-5" />
                  </div>
                  <p className="text-xs font-semibold text-slate-300">Click or Search any Location</p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Select any coordinate in Chennai to evaluate point forecasting, confidence intervals, and SHAP feature drivers.
                  </p>
                </div>
              ) : inspectLoading ? (
                <div className="text-center py-12">
                  <div className="animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-2"></div>
                  <p className="text-xs text-slate-400">Computing point ML inference...</p>
                </div>
              ) : selectedPrediction ? (
                <div className="space-y-4">
                  {/* Point Coordinate & Category */}
                  <div className="p-3 bg-slate-950 rounded-2xl border border-slate-800">
                    <div className="text-[11px] text-slate-400">Coordinates:</div>
                    <div className="text-xs font-mono font-bold text-white">
                      {selectedLocation.latitude.toFixed(4)}°N, {selectedLocation.longitude.toFixed(4)}°E
                    </div>
                    <div className="mt-2 flex items-baseline justify-between">
                      <div className="text-2xl font-black" style={{ color: selectedPrediction.color }}>
                        {selectedPrediction.derived_pm25_sub_index ?? selectedPrediction.predicted_aqi ?? 'N/A'}{' '}
                        <span className="text-xs font-bold">Sub-Index</span>
                      </div>
                      <span
                        className="text-xs font-bold px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: `${selectedPrediction.color}25`, color: selectedPrediction.color }}
                      >
                        {selectedPrediction.category}
                      </span>
                    </div>
                  </div>

                  {/* Target & Uncertainty */}
                  <div className="p-3 bg-slate-950/60 rounded-2xl border border-slate-800/80 space-y-1.5 text-xs">
                    <div className="flex justify-between text-slate-400">
                      <span>Forecast PM2.5:</span>
                      <span className="font-semibold text-slate-200">
                        {selectedPrediction.predicted_pm25} {selectedPrediction.unit}
                      </span>
                    </div>
                    <div className="flex justify-between text-slate-400">
                      <span>Ensemble Disagreement Spread:</span>
                      <span className="font-mono text-slate-300">
                        [{selectedPrediction.lower_bound_pm25} - {selectedPrediction.upper_bound_pm25}] {selectedPrediction.unit}
                      </span>
                    </div>
                    {selectedPrediction.empirical_coverage_pct && (
                      <div className="flex justify-between text-slate-400 text-[10px]">
                        <span>Holdout Coverage:</span>
                        <span className="text-slate-300">{selectedPrediction.empirical_coverage_pct}%</span>
                      </div>
                    )}
                    <div className="flex justify-between text-slate-400">
                      <span>Horizon:</span>
                      <span className="font-bold text-indigo-400">{selectedPrediction.horizon}</span>
                    </div>
                  </div>

                  {/* Top SHAP Drivers */}
                  {selectedExplanation && selectedExplanation.positive_contributors.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="text-xs font-bold text-slate-300">Top Statistical Drivers (SHAP)</div>
                        {selectedExplanation.surrogate_model && (
                          <div className="text-[9px] text-slate-500 font-mono">Surrogate: XGBoost</div>
                        )}
                      </div>
                      <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                        {selectedExplanation.positive_contributors.slice(0, 3).map((c, i) => (
                          <div key={i} className="p-2 bg-slate-950 rounded-xl border border-slate-800 text-[11px]">
                            <div className="flex justify-between font-semibold text-slate-200">
                              <span className="truncate pr-1">{c.name}</span>
                              <span className="text-red-400">+{c.impact}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : null}
            </div>

            <div className="pt-4 border-t border-slate-800 text-[10px] text-slate-500">
              Stacking Ensemble: 8 Base Models + Ridge Meta-Learner (TimeSeriesSplit validated).
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
