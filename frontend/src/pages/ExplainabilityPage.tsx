import React, { useEffect, useState } from 'react';
import { fetchGlobalExplanation, fetchPointExplanation } from '../services/api';
import type { LocalExplanationResponse } from '../types/api';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { Cpu, Sparkles, TrendingUp, TrendingDown, FileText } from 'lucide-react';

export const ExplainabilityPage: React.FC = () => {
  const [globalImportance, setGlobalImportance] = useState<any[]>([]);
  const [localExp, setLocalExp] = useState<LocalExplanationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadXAI = async () => {
    setLoading(true);
    try {
      const [gData, lData] = await Promise.all([
        fetchGlobalExplanation(),
        fetchPointExplanation(13.0827, 80.2707)
      ]);
      setGlobalImportance(gData.global_importance.slice(0, 10));
      setLocalExp(lData);
    } catch (err) {
      console.error('Failed to load XAI page', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadXAI();
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Explainable AI (XAI) & Attribution Framework</h3>
            <p className="text-xs text-slate-400">SHAP (SHapley Additive exPlanations) global feature importances and local local prediction attribution.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h4 className="text-sm font-bold text-white">Global Feature Importance (Top 10 Variables)</h4>
          </div>

          <div className="h-[340px] w-full">
            {loading ? (
              <div className="h-full flex items-center justify-center text-xs text-indigo-400">
                Computing SHAP values across dataset...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={globalImportance} layout="vertical" margin={{ top: 5, right: 20, left: 60, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" />
                  <XAxis type="number" stroke="#64748B" tick={{ fontSize: 10 }} />
                  <YAxis type="category" dataKey="name" stroke="#64748B" tick={{ fontSize: 10 }} width={120} />
                  <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '12px', fontSize: '11px' }} />
                  <Bar dataKey="importance" fill="#6366F1" radius={[0, 8, 8, 0]} name="Mean |SHAP Value|" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-5 shadow-xl space-y-4">
          <div className="flex items-center space-x-2 pb-3 border-b border-slate-800">
            <FileText className="w-5 h-5 text-sky-400" />
            <h4 className="text-sm font-bold text-white">Local Prediction Breakdown (Central Chennai)</h4>
          </div>

          {loading || !localExp ? (
            <div className="py-20 text-center text-xs text-indigo-400">
              Generating local SHAP attributions...
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-2">
                <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">
                  Automated Plain-English Explanation
                </span>
                <p className="text-xs text-slate-300 leading-relaxed italic">
                  "{localExp.narrative}"
                </p>
              </div>

              <div className="space-y-2">
                <span className="text-xs font-bold text-red-400 flex items-center space-x-1">
                  <TrendingUp className="w-4 h-4" />
                  <span>Pollution-Increasing Drivers (+SHAP)</span>
                </span>
                <div className="space-y-1.5">
                  {localExp.positive_contributors.map((item, idx) => (
                    <div key={`p-${idx}`} className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 flex items-center justify-between text-xs">
                      <div>
                        <span className="font-semibold text-slate-200 block">{item.name}</span>
                        <span className="text-[10px] text-slate-500">Observed Value: {item.raw_value}</span>
                      </div>
                      <span className="font-extrabold text-red-400">+{item.impact} µg/m³</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <span className="text-xs font-bold text-emerald-400 flex items-center space-x-1">
                  <TrendingDown className="w-4 h-4" />
                  <span>Pollution-Mitigating Drivers (-SHAP)</span>
                </span>
                <div className="space-y-1.5">
                  {localExp.negative_contributors.map((item, idx) => (
                    <div key={`n-${idx}`} className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 flex items-center justify-between text-xs">
                      <div>
                        <span className="font-semibold text-slate-200 block">{item.name}</span>
                        <span className="text-[10px] text-slate-500">Observed Value: {item.raw_value}</span>
                      </div>
                      <span className="font-extrabold text-emerald-400">{item.impact} µg/m³</span>
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
