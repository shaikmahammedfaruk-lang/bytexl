import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  CheckCheck,
  ShieldAlert,
  AlertTriangle,
  Smartphone,
  Network,
  Clock,
  ArrowRight
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { getAlerts, markAlertRead, markAllAlertsRead } from '../services/api';

export default function AlertsPage() {
  const navigate = useNavigate();
  const { selectedBrand, refreshAlertsCount } = useBrand();

  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    if (!selectedBrand) return;
    setLoading(true);
    try {
      const res = await getAlerts({ brand_id: selectedBrand.id });
      setAlerts(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [selectedBrand]);

  const handleMarkRead = async (id, threatId) => {
    try {
      await markAlertRead(id);
      refreshAlertsCount();
      fetchAlerts();
      if (threatId) {
        navigate(`/threats/${threatId}`);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAllRead = async () => {
    if (!selectedBrand) return;
    try {
      await markAllAlertsRead(selectedBrand.id);
      refreshAlertsCount();
      fetchAlerts();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2">
            <Bell className="w-5 h-5 text-rose-400" />
            Security Incident Alerts
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time critical event stream alerting analysts to brand hijacking and rogue applications.
          </p>
        </div>

        <button
          onClick={handleMarkAllRead}
          className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 border border-slate-700"
        >
          <CheckCheck className="w-4 h-4 text-cyan-400" />
          <span>Mark All as Read</span>
        </button>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {alerts.length > 0 ? (
          alerts.map((alert) => (
            <div
              key={alert.id}
              onClick={() => handleMarkRead(alert.id, alert.threat_id)}
              className={`p-4 rounded-xl border cursor-pointer transition-all flex items-center justify-between gap-4 ${
                alert.is_read
                  ? 'bg-slate-900/50 border-slate-800/80 text-slate-400'
                  : 'bg-slate-900 border-rose-500/30 text-white shadow-lg shadow-rose-950/20 hover:border-rose-400'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    alert.severity === 'CRITICAL'
                      ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                      : alert.severity === 'HIGH'
                      ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                      : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                  }`}
                >
                  {alert.category === 'APP_SPOOFING' ? (
                    <Smartphone className="w-4 h-4" />
                  ) : alert.category === 'CAMPAIGN_DETECTED' ? (
                    <Network className="w-4 h-4" />
                  ) : (
                    <ShieldAlert className="w-4 h-4" />
                  )}
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                        alert.severity === 'CRITICAL'
                          ? 'bg-rose-500 text-white'
                          : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
                      }`}
                    >
                      {alert.severity}
                    </span>
                    <h4 className="font-bold text-xs text-white">{alert.title}</h4>
                    {!alert.is_read && (
                      <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                    )}
                  </div>
                  <p className="text-[11px] text-slate-300 mt-0.5">{alert.message}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 flex-shrink-0">
                <span className="text-[10px] text-slate-500 font-mono">
                  {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                <span className="text-xs text-cyan-400 font-semibold flex items-center gap-1">
                  <span>Triage</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          ))
        ) : (
          <div className="p-12 text-center text-slate-500 text-xs">
            No incident alerts recorded. Your brand perimeter is currently secure.
          </div>
        )}
      </div>
    </div>
  );
}
