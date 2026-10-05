import React from 'react';
import { ShieldAlert } from 'lucide-react';

export const ScientificAlert: React.FC = () => {
  return (
    <div className="bg-gradient-to-r from-amber-500/10 via-slate-900 to-indigo-500/10 border border-amber-500/30 rounded-2xl p-4 shadow-lg">
      <div className="flex items-start space-x-3">
        <div className="p-2 bg-amber-500/20 text-amber-400 rounded-xl mt-0.5 shrink-0">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div>
          <h4 className="text-sm font-bold text-amber-300">
            Scientific Framework Rule: Atmospheric Column Density vs. Ground Pollutants
          </h4>
          <p className="mt-1 text-xs text-slate-300 leading-relaxed">
            Sentinel-5P satellite observations provide total atmospheric column number densities (mol/m²), 
            which represent total atmospheric burden rather than surface concentration. In this framework, satellite 
            observations are strictly treated as <strong>predictive features</strong> in ensemble machine learning models 
            to predict ground-level concentrations (µg/m³) and derive <strong>Predicted AQI</strong> via official CPCB sub-index breakpoints.
          </p>
        </div>
      </div>
    </div>
  );
};
