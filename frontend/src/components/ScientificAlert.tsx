import React from 'react';
import { AlertTriangle, CheckCircle, Database } from 'lucide-react';

interface ScientificAlertProps {
  dataMode?: 'demo' | 'manual_import' | 'live';
  freshness?: 'fresh' | 'stale' | 'expired' | 'unavailable';
  showSatelliteNote?: boolean;
}

export const ScientificAlert: React.FC<ScientificAlertProps> = ({
  dataMode = 'demo',
  freshness = 'stale',
  showSatelliteNote = true
}) => {
  return (
    <div className="space-y-3">
      {/* Mode & Provenance Banner */}
      {dataMode === 'demo' ? (
        <div className="bg-amber-950/40 border border-amber-500/40 rounded-2xl p-4 shadow-lg flex items-start space-x-3">
          <div className="p-2 bg-amber-500/20 text-amber-400 rounded-xl mt-0.5 shrink-0">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-black uppercase tracking-wider px-2 py-0.5 rounded bg-amber-500/30 text-amber-300">
                Simulation / Demo Dataset
              </span>
              <span className="text-xs text-amber-400/80 font-mono">
                Freshness: {freshness.toUpperCase()}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-300 leading-relaxed">
              <strong>Mandatory PRD Compliance:</strong> Currently displaying aligned research baseline data.
              No generated or synthetic value is misrepresented as live CPCB data.
              To switch to verified regulatory observations, import official CAAQMS station reports in the{' '}
              <span className="text-amber-200 font-semibold underline cursor-pointer">Data Sources</span> tab.
            </p>
          </div>
        </div>
      ) : (
        <div className="bg-emerald-950/40 border border-emerald-500/40 rounded-2xl p-4 shadow-lg flex items-start space-x-3">
          <div className="p-2 bg-emerald-500/20 text-emerald-400 rounded-xl mt-0.5 shrink-0">
            <CheckCircle className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-black uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-500/30 text-emerald-300">
                Official Ingest Active ({dataMode.replace('_', ' ').toUpperCase()})
              </span>
              <span className="text-xs text-emerald-400 font-mono">
                Status: {freshness.toUpperCase()}
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-300 leading-relaxed">
              Observations validated against official CPCB schemas and verified against Chennai station coordinates.
            </p>
          </div>
        </div>
      )}

      {/* Satellite Guardrail Rule */}
      {showSatelliteNote && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3 shadow-md flex items-start space-x-3">
          <div className="p-1.5 bg-indigo-500/20 text-indigo-400 rounded-lg shrink-0 mt-0.5">
            <Database className="w-4 h-4" />
          </div>
          <p className="text-[11px] text-slate-400 leading-normal">
            <strong className="text-slate-300">Remote Sensing Guardrail (PRD 21.6):</strong> Sentinel-5P TROPOMI observations represent atmospheric column density (mol/m²), not ground-level concentration. They are incorporated solely as offline context or ML predictor features and never substituted for regulatory ground observations.
          </p>
        </div>
      )}
    </div>
  );
};
