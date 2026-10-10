import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  PieChart as PieIcon,
  ShieldAlert,
  Flame,
  CheckCircle2,
  Calendar,
  Share2,
  Smartphone,
  Layers
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend
} from 'recharts';
import { useBrand } from '../context/BrandContext';
import { getAnalytics } from '../services/api';

const TIMEFRAMES = [
  { id: '7d', label: '7 Days' },
  { id: '30d', label: '30 Days' },
  { id: '90d', label: '90 Days' },
];

export default function AnalyticsPage() {
  const { selectedBrand } = useBrand();
  const [timeframe, setTimeframe] = useState('30d');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      if (!selectedBrand) return;
      setLoading(true);
      try {
        const res = await getAnalytics({ brand_id: selectedBrand.id, timeframe });
        setData(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, [selectedBrand, timeframe]);

  const summary = data?.summary || {};

  return (
    <div className="space-y-6">
      {/* Header & Timeframe selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            Digital Risk & Impersonation Analytics
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time database analytics tracking exposure trends, platform prevalence, and customer impact.
          </p>
        </div>

        {/* Timeframe Filter Buttons */}
        <div className="flex items-center gap-1.5 bg-slate-900 p-1 rounded-xl border border-slate-800 text-xs">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf.id}
              onClick={() => setTimeframe(tf.id)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                timeframe === tf.id
                  ? 'bg-cyan-500 text-slate-950 font-bold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] font-bold uppercase text-slate-400 block">Total Threats</span>
          <div className="text-2xl font-black text-white mt-1">{summary.total_threats || 0}</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-rose-900/30">
          <span className="text-[10px] font-bold uppercase text-rose-400 block">Critical Threats</span>
          <div className="text-2xl font-black text-rose-400 mt-1">{summary.critical_threats || 0}</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-blue-900/30">
          <span className="text-[10px] font-bold uppercase text-blue-400 block">Social Threats</span>
          <div className="text-2xl font-black text-blue-300 mt-1">{summary.social_threats || 0}</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-purple-900/30">
          <span className="text-[10px] font-bold uppercase text-purple-400 block">App Threats</span>
          <div className="text-2xl font-black text-purple-300 mt-1">{summary.app_threats || 0}</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-indigo-900/30">
          <span className="text-[10px] font-bold uppercase text-indigo-400 block">Active Campaigns</span>
          <div className="text-2xl font-black text-indigo-300 mt-1">{summary.active_campaigns || 0}</div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/80 border border-emerald-900/30">
          <span className="text-[10px] font-bold uppercase text-emerald-400 block">Resolved / Mitigated</span>
          <div className="text-2xl font-black text-emerald-400 mt-1">{summary.resolved_threats || 0}</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Threat Trend Chart */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            Detection Velocity Trend
          </h3>
          <div className="h-64 pt-2">
            {data?.threat_trend && data.threat_trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.threat_trend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                  />
                  <Area type="monotone" dataKey="total" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.2} name="Total" />
                  <Area type="monotone" dataKey="social" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} name="Social" />
                  <Area type="monotone" dataKey="apps" stroke="#a855f7" fill="#a855f7" fillOpacity={0.15} name="Apps" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">No trend data.</div>
            )}
          </div>
        </div>

        {/* Risk Distribution Donut Chart */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <PieIcon className="w-4 h-4 text-rose-400" />
            Risk Severity Distribution
          </h3>
          <div className="h-64 pt-2">
            {data?.risk_distribution && data.risk_distribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.risk_distribution}
                    dataKey="count"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                  >
                    {data.risk_distribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">No distribution data.</div>
            )}
          </div>
        </div>

        {/* Threats by Platform */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            Threats by Channel & Ecosystem
          </h3>
          <div className="h-64 pt-2">
            {data?.threats_by_platform && data.threats_by_platform.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.threats_by_platform}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="platform" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={10} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                  />
                  <Bar dataKey="count" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">No platform data.</div>
            )}
          </div>
        </div>

        {/* Threat Types Breakdown */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            Threat Typology Classification
          </h3>
          <div className="h-64 pt-2">
            {data?.threat_types && data.threat_types.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.threat_types} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                  <XAxis type="number" stroke="#64748b" fontSize={10} />
                  <YAxis dataKey="type" type="category" stroke="#64748b" fontSize={10} width={130} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                  />
                  <Bar dataKey="count" fill="#ec4899" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">No type breakdown data.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
