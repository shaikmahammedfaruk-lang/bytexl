import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Network,
  Share2,
  Smartphone,
  Building,
  Flame,
  ShieldAlert,
  ArrowRight,
  ExternalLink,
  RefreshCw,
  GitBranch,
  Layers,
  UserCheck
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { getCampaigns, recorrelateCampaigns } from '../services/api';

export default function CampaignsPage() {
  const navigate = useNavigate();
  const { selectedBrand } = useBrand();

  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recorrelating, setRecorrelating] = useState(false);

  const fetchCampaigns = async () => {
    if (!selectedBrand) return;
    setLoading(true);
    try {
      const res = await getCampaigns(selectedBrand.id);
      setCampaigns(res.data);
      if (res.data.length > 0 && !selectedCampaign) {
        setSelectedCampaign(res.data[0]);
      } else if (res.data.length > 0 && selectedCampaign) {
        const found = res.data.find((c) => c.id === selectedCampaign.id) || res.data[0];
        setSelectedCampaign(found);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCampaigns();
  }, [selectedBrand]);

  const handleRecorrelate = async () => {
    if (!selectedBrand) return;
    setRecorrelating(true);
    try {
      await recorrelateCampaigns(selectedBrand.id);
      await fetchCampaigns();
    } catch (err) {
      console.error(err);
    } finally {
      setRecorrelating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Network className="w-5 h-5 text-purple-400" />
            Cross-Platform Threat Campaigns
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Identify multi-vector coordinated impersonation operations spanning Social Media and App Stores.
          </p>
        </div>

        <button
          onClick={handleRecorrelate}
          disabled={recorrelating}
          className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-semibold flex items-center gap-2 border border-slate-700 active:scale-95 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${recorrelating ? 'animate-spin' : ''}`} />
          <span>Re-run Correlation Engine</span>
        </button>
      </div>

      {/* Campaigns Selector Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {campaigns.map((camp) => (
          <div
            key={camp.id}
            onClick={() => setSelectedCampaign(camp)}
            className={`p-5 rounded-2xl border cursor-pointer transition-all ${
              selectedCampaign?.id === camp.id
                ? 'bg-slate-900 border-cyan-500 shadow-xl shadow-cyan-950/30'
                : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                ACTIVE CAMPAIGN
              </span>
              <div className="flex items-center gap-1 text-rose-400 font-black text-sm">
                <Flame className="w-3.5 h-3.5" />
                <span>{camp.campaign_risk}/100</span>
              </div>
            </div>

            <h3 className="font-bold text-sm text-white mt-2">{camp.name}</h3>
            <p className="text-xs text-slate-400 mt-1 line-clamp-2">{camp.description}</p>

            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs mt-3">
              <span className="text-slate-400">
                Coordinated Vectors: <strong className="text-white">{camp.threat_count} threats</strong>
              </span>
              <div className="flex items-center gap-1">
                {camp.platforms?.map((p, i) => (
                  <span key={i} className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-cyan-300">
                    {p}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Visual Relationship Campaign Graph & Nodes */}
      {selectedCampaign && (
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center gap-2">
                <GitBranch className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                  Visual Threat Correlation Graph
                </h3>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Multi-channel attack topology mapping {selectedBrand?.name} to threat vectors and publisher actors
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Campaign Risk:</span>
              <span className="text-base font-black text-rose-400 px-2.5 py-0.5 rounded bg-rose-500/10 border border-rose-500/20">
                {selectedCampaign.campaign_risk}/100 CRITICAL
              </span>
            </div>
          </div>

          {/* Interactive Visual Graph Canvas */}
          <div className="p-6 rounded-2xl bg-slate-950 border border-slate-800 relative overflow-hidden flex flex-col items-center">
            {/* Ambient Background Grid */}
            <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b08_1px,transparent_1px),linear-gradient(to_bottom,#1e293b08_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />

            {/* Root Brand Node */}
            <div className="relative z-10 flex flex-col items-center">
              <div className="p-3.5 px-6 rounded-2xl bg-gradient-to-br from-cyan-600 to-blue-700 border-2 border-cyan-400 shadow-xl shadow-cyan-500/20 text-center text-white">
                <div className="flex items-center justify-center gap-2">
                  <Building className="w-4 h-4" />
                  <span className="font-bold text-xs uppercase tracking-wider">TARGET BRAND</span>
                </div>
                <h4 className="text-base font-black mt-0.5">{selectedBrand?.name}</h4>
              </div>

              {/* Connecting Conduits / Branch Line */}
              <div className="w-0.5 h-10 bg-gradient-to-b from-cyan-400 to-slate-700 relative">
                <div className="w-2 h-2 rounded-full bg-cyan-400 absolute -top-1 -left-[3px] animate-ping" />
              </div>
            </div>

            {/* Impersonation Endpoints & Developer Nodes */}
            <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl pt-2">
              {selectedCampaign.nodes
                ?.filter((n) => n.id !== 'brand_root')
                .map((node) => {
                  const isApp = node.type === 'app';
                  const isDev = node.type === 'developer';
                  return (
                    <div
                      key={node.id}
                      onClick={() => !isDev && navigate(`/threats/${node.id}`)}
                      className={`p-4 rounded-xl border relative transition-all ${
                        isDev
                          ? 'bg-slate-900/90 border-slate-700/80 text-slate-300'
                          : 'bg-slate-900 border-rose-500/40 hover:border-rose-400 cursor-pointer shadow-lg hover:shadow-rose-950/20'
                      }`}
                    >
                      {/* Connection Dot */}
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full bg-cyan-400" />

                      <div className="flex items-center justify-between text-[10px] mb-2">
                        <span className="font-bold uppercase tracking-wider text-slate-400">
                          {isDev ? 'Threat Actor / Publisher' : node.platform}
                        </span>
                        {!isDev && (
                          <span className="px-1.5 py-0.2 rounded font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                            {node.risk}/100 RISK
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2.5">
                        {isDev ? (
                          <UserCheck className="w-5 h-5 text-amber-400 flex-shrink-0" />
                        ) : isApp ? (
                          <Smartphone className="w-5 h-5 text-purple-400 flex-shrink-0" />
                        ) : (
                          <Share2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                        )}
                        <div className="truncate">
                          <h5 className="font-bold text-xs text-white truncate">{node.label}</h5>
                          <p className="text-[10px] text-slate-400 font-mono truncate">
                            {isDev ? 'Entity publishing rogue assets' : node.threat_type || 'Impersonator'}
                          </p>
                        </div>
                      </div>

                      {!isDev && (
                        <div className="mt-3 pt-2 border-t border-slate-800 flex items-center justify-between text-[10px] text-cyan-400 font-semibold">
                          <span>Inspect Node Telemetry</span>
                          <ArrowRight className="w-3 h-3" />
                        </div>
                      )}
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Campaign Synopsis */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
            <h5 className="font-bold text-slate-200">Correlation Assessment:</h5>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              This campaign exhibits high cross-platform coordination. The threat actors have systematically duplicated brand trademarks across both social communication channels and unauthorized mobile apps to maximize social-engineering surface area.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
