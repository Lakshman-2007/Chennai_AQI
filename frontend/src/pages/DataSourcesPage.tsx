import React, { useEffect, useState } from 'react';
import { fetchDataSources, fetchDataQuality, uploadCPCBCsv, fetchDataSourcesStatus } from '../services/api';
import type { DataSourceInfo, ImportManifest, SourceHealthItem } from '../types/api';
import { Database, CheckCircle, Shield, Upload, FileCheck, AlertCircle, RefreshCw } from 'lucide-react';
import { ScientificAlert } from '../components/ScientificAlert';

export const DataSourcesPage: React.FC = () => {
  const [sources, setSources] = useState<DataSourceInfo[]>([]);
  const [sourcesStatus, setSourcesStatus] = useState<SourceHealthItem[]>([]);
  const [quality, setQuality] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Manual Import State (FR-02)
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [originText, setOriginText] = useState<string>('CPCB CAAQMS Portal Manual Download');
  const [uploading, setUploading] = useState<boolean>(false);
  const [importResult, setImportResult] = useState<ImportManifest | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [srcData, qData, statusData] = await Promise.all([
        fetchDataSources(),
        fetchDataQuality(),
        fetchDataSourcesStatus()
      ]);
      setSources(srcData);
      setQuality(qData);
      setSourcesStatus(statusData.sources || []);
    } catch (err) {
      console.error('Failed to load data sources page', err);
      setError('Unable to load data source catalog and health status.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setImportError(null);
    setImportResult(null);

    try {
      const manifest = await uploadCPCBCsv(selectedFile, originText);
      setImportResult(manifest);
      setSelectedFile(null);
      // Reload quality and sources to reflect updated counts
      loadData();
    } catch (err: any) {
      console.error('Manual import failed', err);
      setImportError(err.response?.data?.detail || 'Failed to parse and import CSV file.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      <ScientificAlert showSatelliteNote={false} />

      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-indigo-600/20 text-indigo-400 rounded-2xl border border-indigo-500/30">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-white">Data Sourcing, Provenance & Ingestion Engine</h3>
            <p className="text-xs text-slate-400">
              Manage provider adapters, inspect freshness TTLs, and import official CPCB CAAQMS reports.
            </p>
          </div>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold border border-slate-700 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-indigo-400 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Refreshing...' : 'Refresh Status'}</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-950/40 border border-red-500/30 rounded-2xl flex items-center justify-between text-xs text-red-300">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span>{error}</span>
          </div>
          <button onClick={loadData} className="px-3 py-1 bg-red-600/30 hover:bg-red-600 text-white rounded-lg font-semibold">
            Retry
          </button>
        </div>
      )}

      {/* Manual CSV Ingestion Form (P0 FR-02) */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 border border-indigo-500/30 rounded-3xl p-6 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 pb-2 border-b border-slate-800">
          <Upload className="w-5 h-5 text-indigo-400" />
          <div>
            <h4 className="text-sm font-bold text-white">Manual Official CPCB / CAAQMS CSV Ingestion (P0 FR-02)</h4>
            <p className="text-xs text-slate-400">
              Upload official station observation exports. Generates SHA-256 manifest, validates physical ranges, and rejects invalid rows with audit reasons.
            </p>
          </div>
        </div>

        <form onSubmit={handleFileUpload} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">Select Official CSV File</label>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer bg-slate-950 p-1.5 rounded-xl border border-slate-800"
              required
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5">Source URL / Authority Origin</label>
            <input
              type="text"
              value={originText}
              onChange={(e) => setOriginText(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
              placeholder="e.g. CPCB CAAQMS Portal"
            />
          </div>

          <button
            type="submit"
            disabled={!selectedFile || uploading}
            className="py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-xs transition-all shadow-lg shadow-emerald-600/20 disabled:opacity-50"
          >
            {uploading ? 'Processing & Auditing Rows...' : 'Import Official CSV'}
          </button>
        </form>

        {importError && (
          <div className="p-3 bg-red-950/40 border border-red-500/30 rounded-xl text-xs text-red-300 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{importError}</span>
          </div>
        )}

        {/* Import Manifest Display */}
        {importResult && (
          <div className="bg-slate-950 p-4 rounded-2xl border border-emerald-500/40 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-emerald-400 flex items-center space-x-1.5">
                <FileCheck className="w-4 h-4" />
                <span>Import Succeeded — Immutable Manifest Created</span>
              </span>
              <span className="text-[10px] font-mono text-slate-400">ID: {importResult.import_id.slice(0, 8)}</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="bg-slate-900 p-2.5 rounded-xl border border-slate-800">
                <span className="text-slate-500 block text-[10px]">SHA-256 Checksum</span>
                <span className="font-mono text-slate-200 text-[11px] truncate block" title={importResult.file_sha256}>
                  {importResult.file_sha256.slice(0, 16)}...
                </span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-xl border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Rows Accepted</span>
                <span className="font-mono font-bold text-emerald-400 text-sm">{importResult.rows_accepted}</span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-xl border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Rows Rejected</span>
                <span className="font-mono font-bold text-red-400 text-sm">{importResult.rows_rejected}</span>
              </div>
              <div className="bg-slate-900 p-2.5 rounded-xl border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Pollutants Verified</span>
                <span className="font-bold text-white text-xs">{importResult.pollutants_found.join(', ')}</span>
              </div>
            </div>

            {Object.keys(importResult.rejection_reasons).length > 0 && (
              <div className="text-[11px] text-slate-400 bg-slate-900 p-2.5 rounded-xl border border-slate-800">
                <span className="font-semibold text-slate-300">Row Rejection Breakdown:</span>
                <div className="flex flex-wrap gap-2 mt-1">
                  {Object.entries(importResult.rejection_reasons).map(([reason, count]) => (
                    <span key={reason} className="px-2 py-0.5 rounded bg-slate-950 font-mono text-[10px] text-red-300">
                      {reason}: {count}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Quality Certification Matrix */}
      {quality && (
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-3">
          <div className="flex items-center space-x-2 text-indigo-400 font-bold text-xs">
            <Shield className="w-4 h-4" />
            <span>Data Quality & Integrity Certification</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
              <span className="text-slate-500 block">Total Normalized Observations</span>
              <span className="text-xl font-black text-white mt-1 block">{quality.total_records}</span>
            </div>

            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
              <span className="text-slate-500 block">Data Completeness Score</span>
              <span className="text-xl font-black text-emerald-400 mt-1 block">{quality.completeness_score}%</span>
            </div>

            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
              <span className="text-slate-500 block">Missingness Percentage</span>
              <span className="text-xl font-black text-slate-300 mt-1 block">{quality.missing_data_percentage}%</span>
            </div>

            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
              <span className="text-slate-500 block">Ground Monitoring Stations</span>
              <span className="text-xl font-black text-sky-400 mt-1 block">{quality.total_stations} Active</span>
            </div>
          </div>
        </div>
      )}

      {/* Live TTL & Source Health State Machine (FR-04, FR-05) */}
      {sourcesStatus.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-3">
          <div className="flex items-center space-x-2 text-sky-400 font-bold text-xs">
            <CheckCircle className="w-4 h-4" />
            <span>Adapter Health & Data Freshness State Machine (FR-04 & PRD 21.5)</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            {sourcesStatus.map((s) => (
              <div key={s.source_id} className="p-3.5 bg-slate-950 rounded-2xl border border-slate-800 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-xs">{s.name}</span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-sky-300">
                    {s.freshness.toUpperCase()}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400">
                  Mode: <span className="font-semibold text-slate-200">{s.mode}</span> • Status: <span className="text-emerald-400 font-semibold">{s.status}</span>
                </div>
                <div className="text-[10px] text-slate-500 font-mono">
                  TTL Threshold: {s.stale_threshold_hours}h • Age: {s.age_seconds ? `${Math.round(s.age_seconds)}s` : 'N/A'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Registered Data Sources Cards */}
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
                <span className="text-slate-500 block font-semibold text-[10px] uppercase tracking-wider">Access Method</span>
                <span className="font-mono text-slate-300 text-[11px]">{src.access_method}</span>
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

              <div className="text-[10px] text-slate-500 italic pt-1">
                Attribution: {src.attribution}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
