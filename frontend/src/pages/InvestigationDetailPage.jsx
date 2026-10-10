import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  SearchCode,
  FileText,
  CheckCircle2,
  Clock,
  ShieldAlert,
  AlertTriangle,
  Flame,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { getInvestigation } from '../services/api';

export default function InvestigationDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { openEvidenceModal } = useBrand();

  const [inv, setInv] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInv = async () => {
      setLoading(true);
      try {
        const res = await getInvestigation(id);
        setInv(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchInv();
  }, [id]);

  if (loading) return <div className="p-8 text-center text-slate-400">Loading case file...</div>;
  if (!inv) return <div className="p-8 text-center text-rose-400">Investigation dossier not found.</div>;

  return (
    <div className="space-y-6">
      {/* Back button */}
      <button
        onClick={() => navigate('/investigations')}
        className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Investigations</span>
      </button>

      {/* Case Header */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-cyan-400 px-2.5 py-1 rounded bg-slate-950 border border-slate-800">
              {inv.case_number}
            </span>
            <span className="px-2.5 py-1 rounded text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
              {inv.status}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => openEvidenceModal(inv.threat_id)}
              className="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md shadow-cyan-500/20"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Generate Evidence Package</span>
            </button>
            <button
              onClick={() => navigate(`/threats/${inv.threat_id}`)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
            >
              Inspect Source Threat
            </button>
          </div>
        </div>

        <h1 className="text-xl font-bold text-white">{inv.title}</h1>
        <p className="text-xs text-slate-400">
          Lead Analyst: <strong className="text-slate-200">{inv.analyst}</strong> • Opened on {new Date(inv.created_at).toLocaleString()}
        </p>
      </div>

      {/* WHAT HAPPENED? */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-400" />
          What Happened? (Executive Threat Summary)
        </h3>
        <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800">
          {inv.summary}
        </p>
      </div>

      {/* WHY DETECTED & EVIDENCE COLLECTED */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Evidence Items */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            Evidence Items Preserved
          </h3>
          <div className="space-y-2">
            {inv.evidence_items?.map((item, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-xs flex justify-between gap-2">
                <span className="font-bold text-slate-400 uppercase text-[10px]">{item.type}</span>
                <span className="font-mono text-slate-200 text-right truncate">{item.detail}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recommended Actions */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            Recommended Triage Actions
          </h3>
          <div className="space-y-2">
            {inv.recommended_actions?.map((act, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-500/20 text-xs text-emerald-200 flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                <span>{act}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* INVESTIGATION TIMELINE */}
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Clock className="w-4 h-4 text-purple-400" />
          Forensic Timeline & Sequence of Events
        </h3>
        <div className="space-y-3 pl-2">
          {inv.timeline?.map((step, idx) => (
            <div key={idx} className="flex items-start gap-3 relative">
              <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 mt-1 flex-shrink-0" />
              <div className="text-xs space-y-0.5">
                <span className="text-[10px] text-slate-500 font-mono">
                  {new Date(step.time).toLocaleTimeString()} • {new Date(step.time).toLocaleDateString()}
                </span>
                <p className="text-slate-300 font-medium">{step.event}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
