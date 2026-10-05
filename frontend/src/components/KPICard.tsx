import React from 'react';
import { TrendingUp } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: number | string;
  unit?: string;
  category?: string;
  color?: string;
  subtext?: string;
  trend?: string;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  unit,
  category,
  color = '#6366F1',
  subtext,
  trend
}) => {
  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl relative overflow-hidden group hover:border-slate-700 transition-all duration-300">
      <div
        className="absolute top-0 left-0 right-0 h-1 transition-all duration-300"
        style={{ backgroundColor: color }}
      />

      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          {title}
        </span>
        {category && (
          <span
            className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide uppercase shadow-sm"
            style={{ backgroundColor: `${color}20`, color: color, borderColor: `${color}40` }}
          >
            {category}
          </span>
        )}
      </div>

      <div className="mt-3 flex items-baseline space-x-2">
        <span className="text-3xl font-extrabold text-white tracking-tight">
          {value}
        </span>
        {unit && (
          <span className="text-xs font-medium text-slate-400">
            {unit}
          </span>
        )}
      </div>

      {subtext && (
        <p className="mt-2 text-xs text-slate-400 font-normal leading-relaxed line-clamp-2">
          {subtext}
        </p>
      )}

      {trend && (
        <div className="mt-3 flex items-center text-[11px] font-medium text-emerald-400 space-x-1">
          <TrendingUp className="w-3.5 h-3.5" />
          <span>{trend}</span>
        </div>
      )}
    </div>
  );
};
