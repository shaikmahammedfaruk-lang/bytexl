import React from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  CheckCircle2,
  ArrowRight,
  FileText,
  Activity,
  ChevronRight
} from 'lucide-react';
import { formatScore } from '../utils/formatters';

export default function RiskScoreCard({ risk, onEscalate, onTakedown }) {
  if (!risk) return null;

  const score = risk.risk_score || 0;
  const category = risk.risk_category || 'Normal';
  const confidence = risk.confidence_score || 90.0;

  const getCategoryTheme = (cat) => {
    switch (cat) {
      case 'Critical Risk':
        return {
          bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
          badge: 'bg-rose-500 text-white',
          bar: 'bg-rose-500',
          icon: ShieldAlert
        };
      case 'High Risk':
        return {
          bg: 'bg-orange-500/10 border-orange-500/30 text-orange-400',
          badge: 'bg-orange-500 text-white',
          bar: 'bg-orange-500',
          icon: AlertTriangle
        };
      case 'Medium Risk':
        return {
          bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
          badge: 'bg-amber-500 text-slate-950',
          bar: 'bg-amber-500',
          icon: AlertTriangle
        };
      case 'Low Risk':
        return {
          bg: 'bg-blue-500/10 border-blue-500/30 text-blue-400',
          badge: 'bg-blue-500 text-white',
          bar: 'bg-blue-500',
          icon: ShieldCheck
        };
      case 'Insufficient Data':
        return {
          bg: 'bg-slate-800 border-slate-700 text-slate-300',
          badge: 'bg-slate-700 text-slate-200',
          bar: 'bg-slate-500',
          icon: HelpCircle
        };
      default: // Normal
        return {
          bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
          badge: 'bg-emerald-500 text-slate-950',
          bar: 'bg-emerald-500',
          icon: ShieldCheck
        };
    }
  };

  const theme = getCategoryTheme(category);
  const Icon = theme.icon;

  return (
    <div className="p-5 rounded-2xl bg-[#0b101e] border border-slate-800 shadow-xl space-y-4">
      {/* Top Banner: Risk Gauge & Category */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-xl border flex items-center justify-center ${theme.bg}`}>
            <Icon className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${theme.badge}`}>
                {category}
              </span>
              <span className="text-[11px] font-mono text-slate-400">
                Confidence: <strong className="text-cyan-400">{formatScore(confidence)}%</strong>
              </span>
            </div>
            <h4 className="text-sm font-bold text-white mt-1">
              Multi-Signal Digital Risk Assessment
            </h4>
          </div>
        </div>

        {/* Big Numerical Score */}
        <div className="text-left sm:text-right">
          <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Risk Score</span>
          <div className="text-2xl font-black text-white font-mono mt-0.5">
            {formatScore(score)}
            <span className="text-xs font-semibold text-slate-500"> / 100</span>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          <span>0.00 (Normal)</span>
          <span>50.00 (Medium)</span>
          <span>100.00 (Critical)</span>
        </div>
        <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden p-0.5 border border-slate-800">
          <div
            className={`h-full rounded-full transition-all duration-700 ${theme.bar}`}
            style={{ width: `${Math.min(100, Math.max(4, score))}%` }}
          />
        </div>
      </div>

      {/* Reasons for Assessment */}
      {risk.reasons && risk.reasons.length > 0 && (
        <div className="space-y-1.5 p-3 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
            Assessment Reasons:
          </span>
          <ul className="space-y-1 text-xs text-slate-300">
            {risk.reasons.map((r, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-cyan-400 font-bold">•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Itemized Evidence Findings */}
      {risk.evidence_findings && risk.evidence_findings.length > 0 && (
        <div className="space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
            Evidence Findings:
          </span>
          <div className="space-y-1.5">
            {risk.evidence_findings.map((item, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-xs flex items-start gap-2">
                <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase tracking-wider flex-shrink-0 ${
                  item.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                  item.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                  item.severity === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                  'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                }`}>
                  {item.category || item.severity}
                </span>
                <span className="text-slate-300 text-[11px] leading-relaxed">{item.detail}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Side-by-Side Official Comparison Snippet */}
      {risk.official_comparison && (
        <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
            Baseline vs Scanned Entity Comparison:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <div className="p-2 rounded-lg bg-emerald-950/20 border border-emerald-500/20">
              <span className="text-[10px] font-bold text-emerald-400 uppercase block">Official Brand Registry</span>
              <p className="font-semibold text-white mt-0.5">{risk.official_comparison.official?.name}</p>
              <p className="text-[11px] font-mono text-slate-400 truncate">{risk.official_comparison.official?.identifier || risk.official_comparison.official?.url}</p>
            </div>
            <div className="p-2 rounded-lg bg-slate-900 border border-slate-700">
              <span className="text-[10px] font-bold text-cyan-400 uppercase block">Scanned Account</span>
              <p className="font-semibold text-white mt-0.5">{risk.official_comparison.scanned?.name}</p>
              <p className="text-[11px] font-mono text-slate-400 truncate">{risk.official_comparison.scanned?.identifier || risk.official_comparison.scanned?.url}</p>
            </div>
          </div>
          {risk.official_comparison.discrepancies && (
            <div className="text-[11px] text-slate-400 space-y-0.5 pt-1">
              {risk.official_comparison.discrepancies.map((d, dIdx) => (
                <p key={dIdx} className="flex items-center gap-1.5">
                  <span className="text-amber-400 font-bold">•</span>
                  <span>{d}</span>
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Recommended Action */}
      <div className="p-3.5 rounded-xl bg-gradient-to-r from-cyan-950/30 to-blue-950/30 border border-cyan-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 block">
            Recommended Next Action:
          </span>
          <p className="text-xs text-slate-200 mt-0.5 font-medium">
            {risk.recommended_action}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {onEscalate && (
            <button
              onClick={onEscalate}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition active:scale-95 flex items-center gap-1.5"
            >
              <FileText className="w-3.5 h-3.5 text-cyan-400" />
              <span>Escalate</span>
            </button>
          )}

          {onTakedown && score >= 50 && (
            <button
              onClick={onTakedown}
              className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-rose-500 to-rose-600 hover:from-rose-400 hover:to-rose-500 text-white text-xs font-bold shadow-md shadow-rose-500/20 transition active:scale-95 flex items-center gap-1.5"
            >
              <span>Takedown Package</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
