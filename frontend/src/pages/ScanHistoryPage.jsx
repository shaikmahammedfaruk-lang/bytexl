import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  History,
  Search,
  Filter,
  Trash2,
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Clock
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { getScanHistory, deleteScanHistoryItem } from '../services/api';
import { formatScore } from '../utils/formatters';
import PlatformSelector, { InstagramIcon, FacebookIcon, XIcon, LinkedInIcon } from '../components/PlatformSelector';

export default function ScanHistoryPage() {
  const navigate = useNavigate();
  const { selectedBrand } = useBrand();

  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlatform, setSelectedPlatform] = useState('ALL');
  const [selectedRisk, setSelectedRisk] = useState('ALL');
  const [search, setSearch] = useState('');

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await getScanHistory({
        brand_id: selectedBrand?.id,
        platform: selectedPlatform !== 'ALL' ? selectedPlatform : undefined,
        risk_category: selectedRisk !== 'ALL' ? selectedRisk : undefined,
        limit: 100
      });
      setHistory(res.data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [selectedBrand, selectedPlatform, selectedRisk]);

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    try {
      await deleteScanHistoryItem(id);
      setHistory(prev => prev.filter(item => item.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  const handleReverify = (item) => {
    navigate('/multi-platform-verification', {
      state: {
        platform: item.platform,
        accountIdentifier: item.profile_url || item.username
      }
    });
  };

  const filteredHistory = history.filter(item => {
    if (!search.trim()) return true;
    const term = search.toLowerCase();
    return (
      item.username?.toLowerCase().includes(term) ||
      item.display_name?.toLowerCase().includes(term) ||
      item.platform?.toLowerCase().includes(term)
    );
  });

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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-cyan-400" />
            Unified Social Scan History
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit log of all multi-platform account verifications, risk assessments, and forensic investigations.
          </p>
        </div>

        <button
          onClick={() => navigate('/multi-platform-verification')}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-bold shadow-md shadow-cyan-500/20 transition active:scale-95 flex items-center gap-1.5"
        >
          <ShieldCheck className="w-4 h-4" />
          <span>New Verification Scan</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-[#0b101e] border border-slate-800 space-y-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <PlatformSelector
            selectedPlatform={selectedPlatform}
            onSelectPlatform={setSelectedPlatform}
            includeAll={true}
          />

          <div className="flex items-center gap-2">
            <select
              value={selectedRisk}
              onChange={(e) => setSelectedRisk(e.target.value)}
              className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="ALL">All Risk Levels</option>
              <option value="Critical Risk">Critical Risk</option>
              <option value="High Risk">High Risk</option>
              <option value="Medium Risk">Medium Risk</option>
              <option value="Low Risk">Low Risk</option>
              <option value="Normal">Normal</option>
            </select>

            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-3 pointer-events-none" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search username or handle..."
                className="pl-8 pr-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* History Table */}
      <div className="rounded-2xl bg-[#0b101e] border border-slate-800 overflow-hidden shadow-xl">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400">Loading audit records...</div>
        ) : filteredHistory.length === 0 ? (
          <div className="p-12 text-center space-y-2">
            <History className="w-10 h-10 text-slate-600 mx-auto" />
            <h4 className="text-sm font-bold text-white">No Scan Records Found</h4>
            <p className="text-xs text-slate-400">
              Run an account verification on Instagram, Facebook, X, or LinkedIn to populate the audit log.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 border-b border-slate-800 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                <tr>
                  <th className="py-3 px-4">Account Entity</th>
                  <th className="py-3 px-4">Platform</th>
                  <th className="py-3 px-4">Official Platform Status</th>
                  <th className="py-3 px-4">Risk Assessment</th>
                  <th className="py-3 px-4">Scanned At</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filteredHistory.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-900/50 transition">
                    <td className="py-3 px-4">
                      <div>
                        <span className="font-bold text-white block">{item.display_name}</span>
                        <span className="font-mono text-cyan-400 text-[11px]">{item.username}</span>
                      </div>
                    </td>

                    <td className="py-3 px-4">
                      <span className="px-2.5 py-1 rounded-lg text-[10px] font-bold bg-slate-900 border border-slate-800 text-slate-300 flex items-center gap-1.5 w-max">
                        {getPlatformIcon(item.platform)}
                        {item.platform}
                      </span>
                    </td>

                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        item.official_platform_verification === 'Verified'
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30'
                          : 'bg-slate-800 text-slate-400 border border-slate-700'
                      }`}>
                        {item.official_platform_verification}
                      </span>
                    </td>

                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          item.risk_category === 'Critical Risk' ? 'bg-rose-500 text-white' :
                          item.risk_category === 'High Risk' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                          item.risk_category === 'Medium Risk' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
                          'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        }`}>
                          {item.risk_category}
                        </span>
                        <span className="font-mono font-bold text-white text-xs">
                          {formatScore(item.risk_score)}/100
                        </span>
                      </div>
                    </td>

                    <td className="py-3 px-4 text-slate-400 text-[11px] font-mono">
                      {new Date(item.scanned_at).toLocaleString()}
                    </td>

                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleReverify(item)}
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
                          title="Re-verify Account"
                        >
                          <RotateCcw className="w-3.5 h-3.5 text-cyan-400" />
                        </button>

                        <button
                          onClick={(e) => handleDelete(item.id, e)}
                          className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-900/50 text-slate-400 hover:text-rose-400 transition"
                          title="Delete Record"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
