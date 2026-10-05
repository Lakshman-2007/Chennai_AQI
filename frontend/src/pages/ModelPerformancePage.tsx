import React, { useEffect, useState } from 'react';
import { fetchModelPerformance } from '../services/api';
import type { ModelPerformanceResponse } from '../types/api';
import { ShieldCheck, Award, CheckCircle2 } from 'lucide-react';

export const ModelPerformancePage: React.FC = () => {
  const [perf, setPerf] = useState<ModelPerformanceResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadPerf = async () => {
    setLoading(true);
    try {
      const data = await fetchModelPerformance();
      setPerf(data);
    } catch (err) {
      console.error('Failed to load model performance', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPerf();
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Machine Learning Model Benchmark & Stacking Weights</h3>
            <p className="text-xs text-slate-400">Automated evaluation across 8 base candidate algorithms and Out-of-Fold Stacking Meta-Learner.</p>
          </div>
        </div>

        {perf && (
          <div className="bg-emerald-500/10 border border-emerald-500/30 px-3.5 py-1.5 rounded-full flex items-center space-x-2 text-xs text-emerald-400 font-bold">
            <Award className="w-4 h-4" />
            <span>Best Model: {perf.best_model} (R² = {perf.best_r2})</span>
          </div>
        )}
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
        <h4 className="text-base font-extrabold text-white">Model Comparison Matrix</h4>

        {loading || !perf ? (
          <div className="py-16 text-center text-xs text-indigo-400">Loading benchmark metrics...</div>
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
                  <th className="py-3 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {perf.comparison.map((m, idx) => {
                  const isBest = m.model === perf.best_model;
                  return (
                    <tr key={idx} className={`hover:bg-slate-800/40 transition-colors ${isBest ? 'bg-indigo-600/10' : ''}`}>
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
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${isBest ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>
                          {isBest ? 'Champion' : 'Candidate'}
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
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-xl space-y-3">
            <h4 className="text-sm font-bold text-white">Stacking Meta-Learner Weights</h4>
            <div className="space-y-2">
              {Object.entries(perf.ensemble_weights).map(([name, weight]) => (
                <div key={name} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-300">{name}</span>
                    <span className="text-indigo-400 font-mono">{(weight * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-indigo-500 to-sky-400" style={{ width: `${weight * 100}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-xl space-y-3">
            <h4 className="text-sm font-bold text-white">Experimental Setup & Validation Strategy</h4>
            <div className="space-y-2 text-xs text-slate-300">
              <div className="flex justify-between bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                <span className="text-slate-400">Target Variable:</span>
                <span className="font-bold text-white">{perf.metadata.target_variable}</span>
              </div>
              <div className="flex justify-between bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                <span className="text-slate-400">Training Samples:</span>
                <span className="font-bold text-white">{perf.metadata.num_train_samples}</span>
              </div>
              <div className="flex justify-between bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                <span className="text-slate-400">Test Samples:</span>
                <span className="font-bold text-white">{perf.metadata.num_test_samples}</span>
              </div>
              <div className="flex justify-between bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                <span className="text-slate-400">Validation Split:</span>
                <span className="font-bold text-indigo-400">Temporal Split + 5-Fold Out-of-Fold (OOF)</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
