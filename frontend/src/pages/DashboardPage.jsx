import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  Flame,
  AlertOctagon,
  AlertTriangle,
  Info,
  Share2,
  Smartphone,
  TrendingUp,
  BarChart2,
  PlusCircle,
  Link2,
  FileCheck,
  Eye,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowRight
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid
} from 'recharts';
import { useBrand } from '../context/BrandContext';
import { getAnalytics, getThreats, resolveThreat, markThreatReviewed } from '../services/api';
import { formatScore } from '../utils/formatters';

export default function DashboardPage() {
  const navigate = useNavigate();
  const {
    selectedBrand,
    openScanModal,
    setIsAddBrandOpen,
    openEvidenceModal,
    handleLoadDemo
  } = useBrand();

  const [analytics, setAnalytics] = useState(null);
  const [recentThreats, setRecentThreats] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    if (!selectedBrand) return;
    setLoading(true);
    try {
      const [analyticsRes, threatsRes] = await Promise.all([
        getAnalytics({ brand_id: selectedBrand.id, timeframe: '30d' }),
        getThreats({ brand_id: selectedBrand.id })
      ]);
      setAnalytics(analyticsRes.data);
      setRecentThreats(threatsRes.data.slice(0, 6));
    } catch (err) {
      console.error("Failed to load dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [selectedBrand]);

  const handleResolve = async (id, e) => {
    e.stopPropagation();
    try {
      await resolveThreat(id);
      fetchDashboardData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkReviewed = async (id, e) => {
    e.stopPropagation();
    try {
      await markThreatReviewed(id);
      fetchDashboardData();
    } catch (err) {
      console.error(err);
    }
  };

  const summary = analytics?.summary || {
    total_threats: 0,
    critical_threats: 0,
    high_threats: 0,
    medium_threats: 0,
    low_threats: 0,
    social_threats: 0,
    app_threats: 0,
    active_campaigns: 0
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Greetings */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-[#0d1424] to-slate-900 border border-slate-800 p-6 rounded-2xl relative overflow-hidden shadow-lg">
        <div className="relative z-10">
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white">
              Good morning, Team
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Live Protection
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Here's what's happening with <strong className="text-cyan-300 font-semibold">{selectedBrand?.name || 'your brand'}</strong>'s digital presence.
          </p>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex flex-wrap items-center gap-2 relative z-10">
          <button
            onClick={() => setIsAddBrandOpen(true)}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 border border-slate-700 transition"
          >
            <PlusCircle className="w-3.5 h-3.5 text-cyan-400" />
            <span>+ Add Brand</span>
          </button>
          <button
            onClick={() => openScanModal('https://instagram.com/')}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 border border-slate-700 transition"
          >
            <Share2 className="w-3.5 h-3.5 text-blue-400" />
            <span>Scan Social</span>
          </button>
          <button
            onClick={() => openScanModal('https://play.google.com/store/apps/')}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 border border-slate-700 transition"
          >
            <Smartphone className="w-3.5 h-3.5 text-emerald-400" />
            <span>Scan App</span>
          </button>
          <button
            onClick={() => openScanModal()}
            className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md shadow-cyan-500/25 transition active:scale-95"
          >
            <Link2 className="w-3.5 h-3.5" />
            <span>Scan Link</span>
          </button>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        {/* TOTAL THREATS */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Threats</span>
            <ShieldAlert className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-white mt-1">{summary.total_threats}</div>
          <span className="text-[10px] text-slate-500 font-medium">All Monitored</span>
        </div>

        {/* CRITICAL */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-rose-900/40 hover:border-rose-700/60 transition">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400">Critical</span>
            <AlertOctagon className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-black text-rose-400 mt-1">{summary.critical_threats}</div>
          <span className="text-[10px] text-rose-500/80 font-medium">Immediate Action</span>
        </div>

        {/* HIGH */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-orange-900/40 hover:border-orange-700/60 transition">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-orange-400">High</span>
            <Flame className="w-4 h-4 text-orange-500" />
          </div>
          <div className="text-2xl font-black text-orange-400 mt-1">{summary.high_threats}</div>
          <span className="text-[10px] text-orange-500/80 font-medium">Investigate</span>
        </div>

        {/* MEDIUM */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-amber-900/30 hover:border-amber-700/50 transition">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400">Medium</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-black text-amber-400 mt-1">{summary.medium_threats}</div>
          <span className="text-[10px] text-amber-500/80 font-medium">Review Needed</span>
        </div>

        {/* LOW */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400">Low</span>
            <Info className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-black text-emerald-400 mt-1">{summary.low_threats}</div>
          <span className="text-[10px] text-emerald-500/80 font-medium">Routine Monitor</span>
        </div>

        {/* SOCIAL THREATS */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-blue-900/40 hover:border-blue-700/60 transition">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400">Social</span>
            <Share2 className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-black text-blue-300 mt-1">{summary.social_threats}</div>
          <span className="text-[10px] text-blue-400/80 font-medium">Profiles & Pages</span>
        </div>

        {/* APP THREATS */}
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-purple-900/40 hover:border-purple-700/60 transition">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">Apps</span>
            <Smartphone className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black text-purple-300 mt-1">{summary.app_threats}</div>
          <span className="text-[10px] text-purple-400/80 font-medium">Stores Spoofed</span>
        </div>
      </div>

      {/* Charts Section: Threat Trend & Platform Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Trend Area Chart */}
        <div className="lg:col-span-2 p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-cyan-400" />
                Threat Detection Velocity (30-Day Trend)
              </h3>
              <p className="text-[11px] text-slate-400">Cumulative count of flagged social and mobile app threats</p>
            </div>
            <div className="flex items-center gap-3 text-[10px]">
              <span className="flex items-center gap-1.5 text-cyan-400">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400"></span> Total
              </span>
              <span className="flex items-center gap-1.5 text-blue-400">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-400"></span> Social
              </span>
              <span className="flex items-center gap-1.5 text-purple-400">
                <span className="w-2.5 h-2.5 rounded-full bg-purple-400"></span> Apps
              </span>
            </div>
          </div>

          <div className="h-64 w-full pt-2">
            {analytics?.threat_trend && analytics.threat_trend.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analytics.threat_trend}>
                  <defs>
                    <linearGradient id="gradTotal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="gradSocial" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={10} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                  />
                  <Area type="monotone" dataKey="total" stroke="#06b6d4" strokeWidth={2} fillOpacity={1} fill="url(#gradTotal)" />
                  <Area type="monotone" dataKey="social" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#gradSocial)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                No telemetry recorded for this timeframe.
              </div>
            )}
          </div>
        </div>

        {/* Threats by Platform Bar Chart */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-purple-400" />
              Threats by Platform
            </h3>
            <p className="text-[11px] text-slate-400">Distribution across ecosystems</p>
          </div>

          <div className="h-64 w-full pt-2">
            {analytics?.threats_by_platform && analytics.threats_by_platform.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics.threats_by_platform} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                  <XAxis type="number" stroke="#64748b" fontSize={10} tickLine={false} />
                  <YAxis dataKey="platform" type="category" stroke="#64748b" fontSize={10} tickLine={false} width={80} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                  />
                  <Bar dataKey="count" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                No platform threat data.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Threats Table */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Flame className="w-4 h-4 text-rose-400" />
              Recent Digital Impersonation Detections
            </h3>
            <p className="text-[11px] text-slate-400">Latest active candidate threats evaluated by multi-signal engine</p>
          </div>
          <button
            onClick={() => navigate('/threat-center')}
            className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
          >
            <span>View All Threats</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase font-bold tracking-wider">
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Name / Entity</th>
                <th className="py-2.5 px-3">Platform</th>
                <th className="py-2.5 px-3">Threat Risk</th>
                <th className="py-2.5 px-3">Customer Impact</th>
                <th className="py-2.5 px-3">Detected</th>
                <th className="py-2.5 px-3">Status</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {recentThreats.length > 0 ? (
                recentThreats.map((threat) => (
                  <tr
                    key={threat.id}
                    onClick={() => navigate(`/threats/${threat.id}`)}
                    className="hover:bg-slate-800/40 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                        {threat.threat_type}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-2.5">
                        <img
                          src={threat.profile_or_icon_url || 'https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=100'}
                          alt=""
                          className="w-7 h-7 rounded-lg object-cover bg-slate-800 border border-slate-700 flex-shrink-0"
                        />
                        <div className="truncate max-w-[200px]">
                          <p className="font-semibold text-slate-200 truncate">{threat.account_or_app_name}</p>
                          <p className="text-[11px] text-slate-500 font-mono truncate">{threat.username_or_package || threat.url}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800/80 text-cyan-300">
                        {threat.platform}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`font-black text-xs ${
                            threat.risk_score >= 71
                              ? 'text-rose-400'
                              : threat.risk_score >= 41
                              ? 'text-orange-400'
                              : 'text-amber-400'
                          }`}
                        >
                          {formatScore(threat.risk_score)}/100
                        </span>
                        <span
                          className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                            threat.risk_score >= 71
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                          }`}
                        >
                          {threat.risk_level}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-amber-400 font-bold">{formatScore(threat.customer_impact_score)}/100</span>
                    </td>
                    <td className="py-3 px-3 text-slate-400 font-mono text-[11px]">
                      {new Date(threat.detected_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          threat.status === 'RESOLVED'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : threat.status === 'REVIEWED'
                            ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                            : threat.status === 'UNDER_INVESTIGATION'
                            ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                            : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        }`}
                      >
                        {threat.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => openEvidenceModal(threat.id)}
                          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-400"
                          title="Generate Evidence"
                        >
                          <FileCheck className="w-3.5 h-3.5" />
                        </button>
                        {threat.status !== 'REVIEWED' && threat.status !== 'RESOLVED' && (
                          <button
                            onClick={(e) => handleMarkReviewed(threat.id, e)}
                            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-semibold"
                          >
                            Review
                          </button>
                        )}
                        {threat.status !== 'RESOLVED' && (
                          <button
                            onClick={(e) => handleResolve(threat.id, e)}
                            className="px-2 py-1 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[10px] font-semibold"
                          >
                            Resolve
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-slate-500 text-xs">
                    No threats detected for this brand yet. Use "Scan Link" or "Load Demo" to simulate monitoring.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
