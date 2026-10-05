import React, { useEffect, useState } from 'react';
import { fetchDataSources, fetchDataQuality } from '../services/api';
import type { DataSourceInfo, DataQualityReport } from '../types/api';
import { Database, CheckCircle, Shield } from 'lucide-react';

export const DataSourcesPage: React.FC = () => {
  const [sources, setSources] = useState<DataSourceInfo[]>([]);
  const [quality, setQuality] = useState<DataQualityReport | null>(null);

  const loadData = async () => {
    try {
      const [srcData, qData] = await Promise.all([
        fetchDataSources(),
        fetchDataQuality()
      ]);
      setSources(srcData);
      setQuality(qData);
    } catch (err) {
      console.error('Failed to load data sources page', err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Multi-Source Data Lineage & Quality Provenance</h3>
            <p className="text-xs text-slate-400">Complete provenance tracking for Sentinel-5P satellite products, CPCB ground stations, and Open-Meteo weather physics.</p>
          </div>
        </div>
      </div>

      {quality && (
        <div className="bg-gradient-to-r from-indigo-950/60 via-slate-900 to-sky-950/60 border border-indigo-500/30 rounded-3xl p-6 shadow-xl space-y-3">
          <div className="flex items-center space-x-2 text-indigo-400 font-bold text-xs">
            <Shield className="w-4 h-4" />
            <span>Data Quality & Integrity Certification</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="bg-slate-950/80 p-3.5 rounded-2xl border border-slate-800">
              <span className="text-slate-500 block">Total Aligned Records</span>
              <span className="text-lg font-black text-white">{quality.total_records}</span>
            </div>

            <div className="bg-slate-950/80 p-3.5 rounded-2xl border border-slate-800">
              <span className="text-slate-500 block">Data Completeness Score</span>
              <span className="text-lg font-black text-emerald-400">{quality.completeness_score}%</span>
            </div>

            <div className="bg-slate-950/80 p-3.5 rounded-2xl border border-slate-800">
              <span className="text-slate-500 block">Missingness Percentage</span>
              <span className="text-lg font-black text-slate-300">{quality.missing_data_percentage}%</span>
            </div>

            <div className="bg-slate-950/80 p-3.5 rounded-2xl border border-slate-800">
              <span className="text-slate-500 block">Ground Monitoring Stations</span>
              <span className="text-lg font-black text-sky-400">{quality.total_stations} Active</span>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {sources.map((src, idx) => (
          <div key={idx} className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl flex flex-col justify-between space-y-4">
            <div>
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                  {src.type}
                </span>
                <span className="text-xs font-semibold text-emerald-400 flex items-center space-x-1">
                  <CheckCircle className="w-3.5 h-3.5" />
                  <span>{src.status}</span>
                </span>
              </div>

              <h4 className="text-base font-extrabold text-white mt-3">{src.name}</h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">{src.description}</p>
            </div>

            <div className="space-y-3 pt-3 border-t border-slate-800 text-xs">
              <div>
                <span className="text-slate-500 block font-semibold text-[10px] uppercase tracking-wider">Provider</span>
                <span className="font-bold text-slate-200">{src.provider}</span>
              </div>

              <div>
                <span className="text-slate-500 block font-semibold text-[10px] uppercase tracking-wider">Variables</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {src.variables.map((v, i) => (
                    <span key={i} className="bg-slate-950 px-2 py-0.5 rounded-md text-[10px] font-mono text-slate-300 border border-slate-800">
                      {v}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <span className="text-slate-500 block font-semibold text-[10px] uppercase tracking-wider">Access Method</span>
                <span className="text-[11px] text-indigo-300 font-mono">{src.access_method}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
