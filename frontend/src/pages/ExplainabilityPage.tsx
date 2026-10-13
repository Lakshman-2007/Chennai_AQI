import React, { useEffect, useState } from 'react';
import { fetchGlobalExplanation, fetchPointExplanation } from '../services/api';
import type { LocalExplanationResponse, GlobalImportanceItem } from '../types/api';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Cpu, Sparkles, TrendingUp, TrendingDown, FileText, ShieldAlert, AlertCircle } from 'lucide-react';
import { ScientificAlert } from '../components/ScientificAlert';

export const ExplainabilityPage: React.FC = () => {
  const [globalImportance, setGlobalImportance] = useState<GlobalImportanceItem[]>([]);
  const [localExp, setLocalExp] = useState<LocalExplanationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadXAI = async () => {
    setLoading(true);
    setError(null);
    try {
      const [gData, lData] = await Promise.all([
        fetchGlobalExplanation(),
        fetchPointExplanation(13.0827, 80.2707)
      ]);
      setGlobalImportance(gData.global_importance.slice(0, 10));
      setLocalExp(lData);
    } catch (err) {
      console.error('Failed to load XAI page', err);
      setError('Failed to compute SHAP explanations. Check model registry status.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadXAI();
  }, []);

  return (
    <div className="space-y-6">
      <ScientificAlert showSatelliteNote={false} />

      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Explainable AI (XAI) & Feature Attributions</h3>
            <p className="text-xs text-slate-400">
              SHAP (SHapley Additive exPlanations) attributing forecast variance to atmospheric physics, satellite columns, and persistence.
            </p>
          </div>
        </div>
      </div>

      {/* Non-causal scientific guardrail */}
      <div className="bg-amber-950/20 border border-amber-500/30 rounded-2xl p-4 flex items-start space-x-3 text-xs text-slate-300">
        <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-amber-300">PRD 8.4 Scientific Integrity Requirement:</strong>
          <p className="mt-0.5 text-slate-400 leading-relaxed">
            Feature attributions reflect statistical model variance shifts relative to baseline expectations. They do not constitute epidemiological or causal proof. Air pollution dynamics are non-linear; attributions quantify model associations only.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-500/30 rounded-2xl flex items-center justify-between text-xs text-red-300">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span>{error}</span>
          </div>
          <button onClick={loadXAI} className="px-3 py-1 bg-red-600/30 hover:bg-red-600 text-white rounded-lg font-semibold">
            Retry
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Global SHAP Importance Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <h4 className="text-sm font-bold text-white">Global Feature Importance (Top 10 Drivers)</h4>
          </div>

          <div className="h-[360px] w-full">
            {loading ? (
              <div className="h-full flex items-center justify-center text-xs text-indigo-400 animate-pulse">
                Evaluating SHAP expectations...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={globalImportance} layout="vertical" margin={{ top: 5, right: 20, left: 70, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis type="number" stroke="#64748B" tick={{ fontSize: 10 }} />
                  <YAxis type="category" dataKey="name" stroke="#64748B" tick={{ fontSize: 10 }} width={140} />
                  <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '12px', fontSize: '11px' }} />
                  <Bar dataKey="importance" fill="#6366F1" radius={[0, 8, 8, 0]} name="Mean |SHAP|" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Local Instance Attribution Breakdown */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
            <FileText className="w-4 h-4 text-sky-400" />
            <h4 className="text-sm font-bold text-white">Local Coordinate Attribution (Central Chennai)</h4>
          </div>

          {loading || !localExp ? (
            <div className="py-24 text-center text-xs text-indigo-400 animate-pulse">
              Generating local SHAP attributions...
            </div>
          ) : (
            <div className="space-y-4">
              {/* Plain-English Narrative */}
              <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-2">
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">
                  Automated Scientific Explanation
                </span>
                <p className="text-xs text-slate-300 leading-relaxed italic">
                  "{localExp.narrative}"
                </p>
              </div>

              {/* Upward Drivers */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-red-400 flex items-center space-x-1">
                  <TrendingUp className="w-4 h-4" />
                  <span>Upward Concentration Drivers (+SHAP)</span>
                </span>
                <div className="space-y-1.5">
                  {localExp.positive_contributors.slice(0, 3).map((item, idx) => (
                    <div key={`p-${idx}`} className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 flex items-center justify-between text-xs">
                      <div>
                        <div className="font-semibold text-white">{item.name}</div>
                        <div className="text-[10px] text-slate-500 font-mono">Recorded: {item.raw_value}</div>
                      </div>
                      <div className="font-mono font-bold text-red-400">+{item.impact} µg/m³</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Moderating Drivers */}
              <div className="space-y-2">
                <span className="text-xs font-bold text-emerald-400 flex items-center space-x-1">
                  <TrendingDown className="w-4 h-4" />
                  <span>Downwards Moderating Drivers (-SHAP)</span>
                </span>
                <div className="space-y-1.5">
                  {localExp.negative_contributors.slice(0, 3).map((item, idx) => (
                    <div key={`n-${idx}`} className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 flex items-center justify-between text-xs">
                      <div>
                        <div className="font-semibold text-white">{item.name}</div>
                        <div className="text-[10px] text-slate-500 font-mono">Recorded: {item.raw_value}</div>
                      </div>
                      <div className="font-mono font-bold text-emerald-400">{item.impact} µg/m³</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
