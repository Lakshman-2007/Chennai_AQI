import React, { useEffect, useState } from 'react';
import { fetchModelPerformance } from '../services/api';
import type { ModelPerformanceResponse } from '../types/api';
import { ShieldCheck, Award, CheckCircle2, FileText, AlertCircle } from 'lucide-react';
import { ScientificAlert } from '../components/ScientificAlert';

export const ModelPerformancePage: React.FC = () => {
  const [perf, setPerf] = useState<ModelPerformanceResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadPerf = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchModelPerformance();
      setPerf(data);
    } catch (err) {
      console.error('Failed to load model performance', err);
      setError('Unable to load model performance and evaluation artifacts.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPerf();
  }, []);

  return (
    <div className="space-y-6">
      <ScientificAlert showSatelliteNote={false} />

      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Walk-Forward Model Benchmark & Model Card</h3>
            <p className="text-xs text-slate-400">
              Evaluated on an untouched chronological holdout using TimeSeriesSplit nested validation (PRD 21.4).
            </p>
          </div>
        </div>

        {perf && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 px-3.5 py-1.5 rounded-full flex items-center space-x-2 text-xs text-emerald-400 font-bold">
            <Award className="w-4 h-4" />
            <span>Best Model: {perf.best_model} (R² = {perf.best_r2})</span>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-500/30 rounded-2xl flex items-center justify-between text-xs text-red-300">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span>{error}</span>
          </div>
          <button onClick={loadPerf} className="px-3 py-1 bg-red-600/30 hover:bg-red-600 text-white rounded-lg font-semibold">
            Retry
          </button>
        </div>
      )}

      {/* Benchmark Matrix Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
        <h4 className="text-base font-extrabold text-white">Holdout Evaluation Matrix vs Baselines</h4>

        {loading || !perf ? (
          <div className="py-16 text-center text-xs text-indigo-400 animate-pulse">Loading benchmark metrics...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-bold">
                  <th className="py-3 px-4">Model Architecture</th>
                  <th className="py-3 px-4">R² Score</th>
                  <th className="py-3 px-4">RMSE (µg/m³)</th>
                  <th className="py-3 px-4">MAE (µg/m³)</th>
                  <th className="py-3 px-4">MAPE (%)</th>
                  <th className="py-3 px-4">Role</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {perf.comparison.map((m, idx) => {
                  const isBest = m.model === perf.best_model;
                  const isBaseline = m.model.startsWith('Baseline');
                  return (
                    <tr
                      key={idx}
                      className={`hover:bg-slate-800/40 transition-colors ${
                        isBest ? 'bg-indigo-600/10' : isBaseline ? 'bg-amber-950/20' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-bold text-slate-200 flex items-center space-x-2">
                        {isBest && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
                        <span>{m.model}</span>
                      </td>
                      <td className={`py-3 px-4 font-mono font-bold ${isBest ? 'text-emerald-400' : 'text-slate-300'}`}>
                        {m.r2.toFixed(4)}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">{m.rmse.toFixed(2)}</td>
                      <td className="py-3 px-4 font-mono text-slate-300">{m.mae.toFixed(2)}</td>
                      <td className="py-3 px-4 font-mono text-slate-300">{m.mape.toFixed(2)}%</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            isBest
                              ? 'bg-emerald-500/20 text-emerald-300'
                              : isBaseline
                              ? 'bg-amber-500/20 text-amber-300'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {isBest ? 'Production Champion' : isBaseline ? 'Benchmark' : 'Candidate'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {perf && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Stacking Weights */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
            <h4 className="text-sm font-bold text-white">Stacking Meta-Learner (Ridge) Weights</h4>
            <div className="space-y-2.5">
              {Object.entries(perf.ensemble_weights).map(([name, weight]) => (
                <div key={name} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-300">{name}</span>
                    <span className="font-mono text-indigo-400">{(weight * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                    <div
                      className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                      style={{ width: `${Math.max(1, weight * 100)}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Model Card Inspector */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
            <div className="flex items-center space-x-2 pb-2 border-b border-slate-800">
              <FileText className="w-4 h-4 text-sky-400" />
              <h4 className="text-sm font-bold text-white">Official Model Card & Validation Summary</h4>
            </div>

            {perf.model_card ? (
              <div className="space-y-3 text-xs">
                <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800 space-y-1.5">
                  <div className="text-[10px] text-slate-400 uppercase font-bold">Model Identity</div>
                  <div className="font-bold text-white text-sm">{perf.model_card.model_details?.name}</div>
                  <div className="text-slate-300">
                    Version: <span className="font-mono text-indigo-400">{perf.model_card.model_details?.version}</span> • Target: {perf.model_card.model_details?.target}
                  </div>
                </div>

                <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800 space-y-1.5">
                  <div className="text-[10px] text-slate-400 uppercase font-bold">Evaluation & Baselines</div>
                  <div className="text-slate-300">
                    Holdout Samples: <span className="font-mono font-bold text-white">{perf.model_card.evaluation_factors?.chronological_holdout_samples}</span>
                  </div>
                  <div className="text-slate-300">
                    RMSE Reduction vs Persistence Baseline:{' '}
                    <span className="font-mono font-bold text-emerald-400">
                      {perf.model_card.evaluation_factors?.baseline_comparison?.percentage_rmse_reduction}%
                    </span>
                  </div>
                </div>

                <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800 space-y-1">
                  <div className="text-[10px] text-slate-400 uppercase font-bold">Intended Scope & Caveats</div>
                  <p className="text-slate-400 text-[11px] leading-relaxed">
                    {perf.model_card.intended_use?.caveats}
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-500 py-6">Model card details loaded from metadata.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
