import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  ChevronDown,
  Building,
  LogOut,
  Menu,
  X
} from 'lucide-react';
import { useBrand } from '../context/BrandContext';
import { useAuth } from '../context/AuthContext';

export default function Header({ onToggleMobileSidebar = () => {}, mobileSidebarOpen = false }) {
  const navigate = useNavigate();
  const {
    brands,
    selectedBrand,
    setSelectedBrand,
    unreadAlertsCount
  } = useBrand();

  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  // Derive initials for avatar
  const displayName = user?.full_name || user?.username || 'SecOps Analyst';
  const roleTitle = user?.role || 'SOC Analyst';
  const initials = displayName
    .split(' ')
    .filter(Boolean)
    .map((n) => n[0])
    .join('')
    .substring(0, 2)
    .toUpperCase() || 'SA';

  return (
    <header className="h-16 bg-[#0a0f1d]/90 backdrop-blur-md border-b border-slate-800/80 px-3 sm:px-6 flex items-center justify-between z-20 flex-shrink-0">
      {/* Left Section: Mobile Hamburger Button & Monitored Brand Selector */}
      <div className="flex items-center gap-2 sm:gap-4">
        {/* Mobile / Tablet Hamburger Toggle Button (Hidden on lg and desktop) */}
        <button
          type="button"
          onClick={onToggleMobileSidebar}
          className="p-2 rounded-xl bg-slate-900 border border-slate-700/80 text-cyan-400 hover:bg-slate-800 hover:border-cyan-500/50 transition-all lg:hidden flex-shrink-0 active:scale-95 shadow-sm"
          aria-label={mobileSidebarOpen ? "Close navigation menu" : "Open navigation menu"}
          title={mobileSidebarOpen ? "Close navigation menu" : "Open navigation menu"}
        >
          {mobileSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* Monitored Brand Selector Dropdown */}
        <div className="relative">
          <label className="text-[9px] sm:text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-0.5 truncate">
            Monitored Brand
          </label>
          <div className="relative inline-flex items-center">
            <Building className="w-3.5 h-3.5 text-cyan-400 absolute left-2 pointer-events-none" />
            <select
              value={selectedBrand?.id || ''}
              onChange={(e) => {
                const found = brands.find((b) => b.id === e.target.value);
                if (found) setSelectedBrand(found);
              }}
              className="pl-7 pr-7 py-1 bg-slate-900 border border-slate-700/80 rounded-md text-xs font-semibold text-slate-200 focus:outline-none focus:border-cyan-500 appearance-none cursor-pointer hover:border-slate-600 shadow-sm max-w-[125px] sm:max-w-[180px] md:max-w-[220px] truncate"
            >
              {brands.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.name}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2 pointer-events-none" />
          </div>
        </div>

        {/* Multi-Signal Engine Status Indicator (Hidden on mobile phones) */}
        <div className="hidden md:flex items-center gap-2 pl-3 border-l border-slate-800">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-[11px] text-slate-400 font-medium whitespace-nowrap">
            Engine: <span className="text-emerald-400 font-semibold">Active</span>
          </span>
        </div>
      </div>

      {/* Right Controls: Alerts Bell, Analyst Profile & Logout */}
      <div className="flex items-center gap-1.5 sm:gap-3 flex-shrink-0">
        {/* Alerts Bell Icon */}
        <button
          onClick={() => navigate('/alerts')}
          className="relative p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition-all flex-shrink-0"
          aria-label="View Alerts"
        >
          <Bell className="w-4 h-4" />
          {unreadAlertsCount > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[9px] font-bold text-white shadow-sm">
              {unreadAlertsCount}
            </span>
          )}
        </button>

        {/* Analyst Avatar & Identity */}
        <button
          type="button"
          onClick={() => navigate('/profile')}
          className="flex items-center gap-2 pl-2 sm:pl-3 border-l border-slate-800 text-left hover:opacity-85 transition group flex-shrink-0"
          title="View User Profile & Account Settings"
        >
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={displayName}
              className="w-8 h-8 rounded-full object-cover border border-cyan-400/40 shadow-inner group-hover:ring-2 group-hover:ring-cyan-400/50 transition flex-shrink-0"
            />
          ) : (
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shadow-inner group-hover:ring-2 group-hover:ring-cyan-400/50 transition flex-shrink-0">
              {initials}
            </div>
          )}
          <div className="hidden xl:block text-left">
            <p className="text-xs font-semibold text-slate-200 leading-tight group-hover:text-cyan-300 transition truncate max-w-[130px]">
              {displayName}
            </p>
            <p className="text-[10px] text-slate-500 leading-tight truncate max-w-[130px]">
              {roleTitle}
            </p>
          </div>
        </button>

        {/* Logout Button */}
        <button
          type="button"
          onClick={handleLogout}
          className="p-2 rounded-lg bg-slate-800/80 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 border border-slate-700/60 transition-all flex-shrink-0"
          title="Sign Out of BrandShield"
          aria-label="Sign Out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
