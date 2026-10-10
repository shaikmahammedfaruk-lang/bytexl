import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  ShieldCheck,
  ShieldAlert,
  BarChart3,
  Layers,
  Share2,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { getReportsSummary, exportAuditReport } from '../services/api';
import { formatScore } from '../utils/formatters';
import { InstagramIcon, FacebookIcon, XIcon, LinkedInIcon } from '../components/PlatformSelector';

export default function ReportsPage() {
  const { selectedBrand } = useBrand();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const res = await getReportsSummary({ brand_id: selectedBrand?.id });
      setSummary(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [selectedBrand]);

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await exportAuditReport({ brand_id: selectedBrand?.id });
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `brandshield-compliance-report-${selectedBrand?.name || 'brand'}-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
    } finally {
      setExporting(false);
    }
  };

  if (loading || !summary) {
    return <div className="p-12 text-center text-xs text-slate-400">Compiling executive risk telemetry...</div>;
  }

  const pb = summary.platform_breakdown || {};
  const rd = summary.risk_distribution || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <FileText className="w-5 h-5 text-cyan-400" />
            Executive Risk & Compliance Reports
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit summary of protected digital assets, cross-platform impersonations, and trademark enforcement metrics.
          </p>
        </div>

        <button
          onClick={handleExport}
          disabled={exporting}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold shadow-md shadow-cyan-500/20 transition active:scale-95 flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          <span>{exporting ? 'Generating Report...' : 'Export Audit Dossier (JSON)'}</span>
        </button>
      </div>

      {/* Top 4 Stat Widgets */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-[#0b101e] border border-slate-800 space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Scans Run</span>
          <div className="text-2xl font-black text-white font-mono">{summary.total_scans}</div>
          <span className="text-[10px] text-slate-500">Multi-Platform Verifications</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#0b101e] border border-slate-800 space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Active Threats</span>
          <div className="text-2xl font-black text-rose-400 font-mono">{summary.active_threats_count}</div>
          <span className="text-[10px] text-slate-500">Flagged Impersonators</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#0b101e] border border-slate-800 space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Duplicates Detected</span>
          <div className="text-2xl font-black text-amber-400 font-mono">{summary.duplicates_detected_count}</div>
          <span className="text-[10px] text-slate-500">Lookalike Permutations</span>
        </div>

        <div className="p-4 rounded-2xl bg-[#0b101e] border border-slate-800 space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Brand Protection Posture</span>
          <div className="text-2xl font-black text-emerald-400 font-mono">{formatScore(summary.compliance_score)}%</div>
          <span className="text-[10px] text-slate-500">Compliance & Defense Score</span>
        </div>
      </div>

      {/* Platform & Risk Distributions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Platform Breakdown */}
        <div className="p-5 rounded-2xl bg-[#0b101e] border border-slate-800 space-y-4 shadow-xl">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Share2 className="w-4 h-4 text-cyan-400" />
            Social Platform Telemetry Breakdown
          </h3>

          <div className="space-y-3">
            {[
              { name: 'Instagram', icon: InstagramIcon, count: pb['Instagram'] || 0, color: 'bg-pink-500' },
              { name: 'Facebook', icon: FacebookIcon, count: pb['Facebook'] || 0, color: 'bg-blue-600' },
              { name: 'X (Twitter)', icon: XIcon, count: pb['X'] || 0, color: 'bg-slate-400' },
              { name: 'LinkedIn', icon: LinkedInIcon, count: pb['LinkedIn'] || 0, color: 'bg-sky-500' }
            ].map((p, idx) => {
              const Icon = p.icon;
              const total = Math.max(1, summary.total_scans);
              const pct = ((p.count / total) * 100);
              return (
                <div key={idx} className="space-y-1 text-xs">
                  <div className="flex justify-between items-center text-slate-300">
                    <span className="flex items-center gap-2 font-medium">
                      <Icon className="w-4 h-4" />
                      {p.name}
                    </span>
                    <span className="font-mono font-bold text-white">{p.count} scans ({formatScore(pct)}%)</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${p.color}`} style={{ width: `${Math.min(100, Math.max(4, pct))}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Risk Distribution */}
        <div className="p-5 rounded-2xl bg-[#0b101e] border border-slate-800 space-y-4 shadow-xl">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            Threat Risk Classification Distribution
          </h3>

          <div className="space-y-3">
            {[
              { label: 'Critical Risk', count: rd['Critical Risk'] || 0, color: 'bg-rose-500', text: 'text-rose-400' },
              { label: 'High Risk', count: rd['High Risk'] || 0, color: 'bg-orange-500', text: 'text-orange-400' },
              { label: 'Medium Risk', count: rd['Medium Risk'] || 0, color: 'bg-amber-500', text: 'text-amber-400' },
              { label: 'Low Risk', count: rd['Low Risk'] || 0, color: 'bg-blue-500', text: 'text-blue-400' },
              { label: 'Normal / Verified', count: rd['Normal'] || 0, color: 'bg-emerald-500', text: 'text-emerald-400' }
            ].map((r, idx) => {
              const total = Math.max(1, summary.total_scans);
              const pct = ((r.count / total) * 100);
              return (
                <div key={idx} className="space-y-1 text-xs">
                  <div className="flex justify-between items-center text-slate-300">
                    <span className={`font-semibold ${r.text}`}>{r.label}</span>
                    <span className="font-mono font-bold text-white">{r.count} accounts ({formatScore(pct)}%)</span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${r.color}`} style={{ width: `${Math.min(100, Math.max(4, pct))}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Compliance Certification Banner */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-950/30 to-cyan-950/30 border border-emerald-500/30 flex items-start gap-3">
        <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
        <div className="text-xs">
          <h4 className="font-bold text-white uppercase tracking-wider">Brand Trademark Protection Status: Active</h4>
          <p className="text-slate-300 mt-1 leading-relaxed">
            Automated multi-signal threat surveillance actively safeguards <strong>{summary.brand_name}</strong> across Instagram, Facebook, X, and LinkedIn.
            All findings adhere to verifiable platform API telemetry and documented trademark infringement evidence packages.
          </p>
        </div>
      </div>
    </div>
  );
}
