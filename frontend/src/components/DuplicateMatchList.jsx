import React from 'react';
import {
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  ExternalLink,
  Users,
  Copy,
  ArrowRight,
  Info,
  CheckCircle2,
  FileText
} from 'lucide-react';
import { formatScore } from '../utils/formatters';
import { InstagramIcon, FacebookIcon, XIcon, LinkedInIcon } from './PlatformSelector';

export default function DuplicateMatchList({
  matches,
  apiNotice,
  referenceAccount,
  onInvestigateMatch
}) {
  if (!matches || matches.length === 0) {
    return (
      <div className="p-8 rounded-2xl bg-[#0b101e] border border-slate-800 text-center space-y-2">
        <ShieldCheck className="w-10 h-10 text-emerald-400 mx-auto" />
        <h4 className="text-sm font-bold text-white">No Suspicious Duplicates Found</h4>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          No duplicate or impersonating profiles exceeding the similarity threshold were detected across the queried platform directory.
        </p>
      </div>
    );
  }

  const getPlatformIcon = (plat) => {
    switch (plat) {
      case 'Instagram':
        return <InstagramIcon className="w-3.5 h-3.5 text-pink-400" />;
      case 'Facebook':
        return <FacebookIcon className="w-3.5 h-3.5 text-blue-400" />;
      case 'X':
        return <XIcon className="w-3.5 h-3.5 text-white" />;
      case 'LinkedIn':
        return <LinkedInIcon className="w-3.5 h-3.5 text-sky-400" />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* Scope / Reference Header */}
      {referenceAccount && (
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2">
          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-medium">Protected Baseline:</span>
            <strong className="text-white font-mono bg-slate-800 px-2 py-0.5 rounded border border-slate-700">
              {referenceAccount.base_handle || referenceAccount.brand}
            </strong>
          </div>
          <span className="text-[11px] font-mono text-cyan-400">
            {matches.length} Potential Duplicates Identified
          </span>
        </div>
      )}

      {/* API Limitations Disclosure */}
      {apiNotice && (
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 flex items-start gap-2.5">
          <Info className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            {apiNotice}
          </p>
        </div>
      )}

      {/* Match Cards List */}
      <div className="space-y-3">
        {matches.map((match) => {
          const sim = match.similarity_score || 0;
          const isCritical = match.impersonation_risk === 'CRITICAL' || sim >= 85;

          return (
            <div
              key={match.id}
              className={`p-4 rounded-xl border transition-all duration-200 bg-[#0b101e] ${
                isCritical
                  ? 'border-rose-500/30 hover:border-rose-500/50 shadow-sm shadow-rose-500/5'
                  : 'border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                {/* Left: Avatar, Username, Platform, and Similarity */}
                <div className="flex items-center gap-3">
                  {match.avatar_url ? (
                    <img
                      src={match.avatar_url}
                      alt={match.display_name}
                      className="w-10 h-10 rounded-xl object-cover border border-slate-700 bg-slate-900 flex-shrink-0"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-slate-300">
                      {match.display_name ? match.display_name[0] : '@'}
                    </div>
                  )}

                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-white text-xs">{match.display_name}</span>
                      <span className="text-[11px] font-mono text-cyan-400">{match.username}</span>

                      {/* Platform Pill */}
                      <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1">
                        {getPlatformIcon(match.platform)}
                        {match.platform}
                      </span>

                      {/* Risk Badge */}
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${
                        match.impersonation_risk === 'CRITICAL' ? 'bg-rose-500 text-white' :
                        match.impersonation_risk === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                        match.impersonation_risk === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                        'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      }`}>
                        {match.impersonation_risk}
                      </span>
                    </div>

                    <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                      {match.bio}
                    </p>
                  </div>
                </div>

                {/* Right: Similarity Score & Actions */}
                <div className="flex items-center gap-3 self-end md:self-auto flex-shrink-0">
                  <div className="text-right">
                    <span className="text-[9px] uppercase font-bold text-slate-500 block">Similarity</span>
                    <span className={`text-base font-black font-mono ${
                      sim >= 85 ? 'text-rose-400' : sim >= 65 ? 'text-amber-400' : 'text-cyan-400'
                    }`}>
                      {formatScore(sim)}%
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {match.profile_url && (
                      <a
                        href={match.profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700 transition"
                        title="Open Candidate Profile in New Tab"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}

                    {onInvestigateMatch && (
                      <button
                        onClick={() => onInvestigateMatch(match)}
                        className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-[11px] font-bold shadow-md shadow-cyan-500/10 transition active:scale-95 flex items-center gap-1"
                      >
                        <span>Investigate</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Evidence Bullets */}
              {match.evidence && match.evidence.length > 0 && (
                <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-x-4 gap-y-1 text-[10px] text-slate-400">
                  {match.evidence.map((ev, eIdx) => (
                    <span key={eIdx} className="flex items-center gap-1">
                      <span className="text-rose-400 font-bold">•</span>
                      <span>{ev}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
