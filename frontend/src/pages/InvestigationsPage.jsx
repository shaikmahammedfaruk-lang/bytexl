import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  SearchCode,
  ArrowRight,
  ShieldAlert,
  Clock,
  User,
  CheckCircle2,
  FileText
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { getInvestigations } from '../services/api';

export default function InvestigationsPage() {
  const navigate = useNavigate();
  const { selectedBrand } = useBrand();

  const [investigations, setInvestigations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInvs = async () => {
      if (!selectedBrand) return;
      setLoading(true);
      try {
        const res = await getInvestigations(selectedBrand.id);
        setInvestigations(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchInvs();
  }, [selectedBrand]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-white flex items-center gap-2">
          <SearchCode className="w-5 h-5 text-cyan-400" />
          AI Threat Investigations
        </h1>
        <p className="text-xs text-slate-400 mt-0.5">
          In-depth SOC investigative dossiers, digital forensic trails, and recommended takedown workflows.
        </p>
      </div>

      {/* Grid of Investigations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {investigations.length > 0 ? (
          investigations.map((inv) => (
            <div
              key={inv.id}
              onClick={() => navigate(`/investigations/${inv.id}`)}
              className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/50 cursor-pointer transition-all hover:shadow-xl hover:shadow-cyan-950/20 flex flex-col justify-between space-y-4 group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] font-bold text-cyan-400 px-2 py-0.5 rounded bg-slate-950 border border-slate-800">
                    {inv.case_number}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      inv.status === 'CLOSED'
                        ? 'bg-emerald-500/20 text-emerald-300'
                        : 'bg-amber-500/20 text-amber-300'
                    }`}
                  >
                    {inv.status}
                  </span>
                </div>

                <h3 className="font-bold text-sm text-white group-hover:text-cyan-300 transition-colors">
                  {inv.title}
                </h3>

                <p className="text-xs text-slate-300 leading-relaxed line-clamp-3 bg-slate-950/50 p-2.5 rounded-lg border border-slate-800/80">
                  {inv.summary}
                </p>

                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800">
                  <span className="flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-cyan-400" />
                    <span>{inv.analyst}</span>
                  </span>
                  <span className="font-mono">{new Date(inv.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs text-cyan-400 font-semibold">
                <span>View Full Case File & Evidence</span>
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          ))
        ) : (
          <div className="col-span-full py-12 text-center text-slate-500 text-xs">
            No active investigations for this brand yet. Click "Investigate" from any threat in Threat Center to open one.
          </div>
        )}
      </div>
    </div>
  );
}
