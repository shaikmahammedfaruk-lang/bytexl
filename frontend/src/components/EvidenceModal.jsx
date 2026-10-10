import React, { useState, useEffect } from 'react';
import {
  X,
  FileText,
  Download,
  Copy,
  Check,
  Printer,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Lock,
  ExternalLink
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { getEvidence, generateEvidence } from '../services/api';
import { formatScore } from '../utils/formatters';

export default function EvidenceModal() {
  const { isEvidenceModalOpen, setIsEvidenceModalOpen, selectedEvidenceThreatId } = useBrand();

  const [evidence, setEvidence] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [copiedJson, setCopiedJson] = useState(false);

  useEffect(() => {
    if (isEvidenceModalOpen && selectedEvidenceThreatId) {
      fetchEvidence();
    }
  }, [isEvidenceModalOpen, selectedEvidenceThreatId]);

  const fetchEvidence = async () => {
    setLoading(true);
    try {
      const res = await generateEvidence(selectedEvidenceThreatId);
      setEvidence(res.data);
    } catch (err) {
      console.error("Failed to generate evidence", err);
    } finally {
      setLoading(false);
    }
  };

  if (!isEvidenceModalOpen) return null;

  const handleCopyNotice = () => {
    if (evidence?.takedown_notice_template) {
      navigator.clipboard.writeText(evidence.takedown_notice_template);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownloadJson = () => {
    if (!evidence) return;
    const blob = new Blob([JSON.stringify(evidence, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${evidence.report_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#0b101e] border border-slate-700/80 rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="p-4 px-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                Certified Digital Risk Evidence Package
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
                  {evidence?.report_id || 'Generating...'}
                </span>
              </h3>
              <p className="text-[11px] text-slate-400">Cryptographically hashed dossier for platform takedown reporting</p>
            </div>
          </div>
          <button
            onClick={() => setIsEvidenceModalOpen(false)}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1 font-sans text-xs">
          {loading ? (
            <div className="py-16 text-center text-slate-400">
              <div className="w-8 h-8 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin mx-auto mb-3" />
              <span>Synthesizing multi-signal telemetry & digital signature...</span>
            </div>
          ) : evidence ? (
            <>
              {/* Integrity & Tamper Protection Badge */}
              <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2 text-[11px]">
                  <Lock className="w-4 h-4 text-emerald-400" />
                  <div>
                    <span className="text-slate-400 font-medium">Digital Signature (SHA-256): </span>
                    <span className="font-mono text-cyan-400 text-[10px] break-all">{evidence.evidence_hash}</span>
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold uppercase whitespace-nowrap">
                  VERIFIED
                </span>
              </div>

              {/* Threat Summary Banner */}
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500 text-white uppercase">
                    {evidence.threat_summary.threat_type}
                  </span>
                  <span className="text-slate-400 text-[11px]">
                    Platform: <strong className="text-slate-200">{evidence.threat_summary.platform}</strong>
                  </span>
                </div>
                <h4 className="text-sm font-bold text-white">{evidence.threat_summary.title}</h4>
                <p className="text-[11px] text-cyan-400 font-mono break-all">{evidence.threat_summary.url}</p>

                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800 text-[11px]">
                  <div>
                    <span className="text-slate-500 block">Threat Risk:</span>
                    <strong className="text-rose-400">{formatScore(evidence.threat_summary.risk_score)}/100</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Customer Impact:</span>
                    <strong className="text-amber-400">{formatScore(evidence.threat_summary.customer_impact_score)}/100</strong>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Detection Confidence:</span>
                    <strong className="text-cyan-400">{formatScore(evidence.threat_summary.confidence)}%</strong>
                  </div>
                </div>
              </div>

              {/* Official vs Suspicious Comparison Audit */}
              {evidence.comparison_audit && (
                <div className="space-y-2">
                  <h5 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">
                    Comparative Trademark & Identity Audit
                  </h5>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/20 space-y-1.5">
                      <div className="flex items-center justify-between text-emerald-400 text-[11px] font-bold uppercase">
                        <span>Legitimate Brand Asset</span>
                        <ShieldCheck className="w-4 h-4" />
                      </div>
                      <p className="font-semibold text-slate-200">{evidence.comparison_audit.official?.name}</p>
                      <p className="text-[11px] text-slate-400 font-mono">{evidence.comparison_audit.official?.username_or_dev}</p>
                      <p className="text-[10px] text-slate-500 font-mono truncate">{evidence.comparison_audit.official?.url}</p>
                    </div>

                    <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-500/20 space-y-1.5">
                      <div className="flex items-center justify-between text-rose-400 text-[11px] font-bold uppercase">
                        <span>Infringing Suspect Asset</span>
                        <AlertTriangle className="w-4 h-4" />
                      </div>
                      <p className="font-semibold text-slate-200">{evidence.comparison_audit.suspicious?.name}</p>
                      <p className="text-[11px] text-slate-400 font-mono">{evidence.comparison_audit.suspicious?.username_or_dev}</p>
                      <p className="text-[10px] text-slate-500 font-mono truncate">{evidence.comparison_audit.suspicious?.url}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Takedown Notice Template */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h5 className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">
                    Ready-to-Submit Abuse & Takedown Notice
                  </h5>
                  <button
                    onClick={handleCopyNotice}
                    className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-400 text-[11px] font-semibold flex items-center gap-1 border border-slate-700 transition"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied Notice' : 'Copy Notice'}</span>
                  </button>
                </div>
                <pre className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 font-mono text-[10px] text-slate-300 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                  {evidence.takedown_notice_template}
                </pre>
              </div>
            </>
          ) : (
            <div className="py-8 text-center text-rose-400">Failed to load evidence report.</div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 px-6 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
          <div className="text-[11px] text-slate-500 font-mono">
            BrandShield AI DRP Preservation Protocol
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 border border-slate-700"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print</span>
            </button>
            <button
              onClick={handleDownloadJson}
              className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-cyan-500/20 transition active:scale-95"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Evidence (JSON)</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
