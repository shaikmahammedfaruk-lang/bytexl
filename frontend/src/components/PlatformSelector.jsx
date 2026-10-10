import React from 'react';

export const InstagramIcon = ({ className = "w-4 h-4" }) => (
  <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect width="20" height="20" x="2" y="2" rx="5" ry="5" />
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
    <line x1="17.5" x2="17.51" y1="6.5" y2="6.5" />
  </svg>
);

export const FacebookIcon = ({ className = "w-4 h-4" }) => (
  <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" className={className}>
    <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
  </svg>
);

export const XIcon = ({ className = "w-4 h-4" }) => (
  <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" className={className}>
    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
  </svg>
);

export const LinkedInIcon = ({ className = "w-4 h-4" }) => (
  <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor" className={className}>
    <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z"/>
  </svg>
);

export const PLATFORMS_CONFIG = [
  { id: 'Instagram', name: 'Instagram', icon: InstagramIcon, color: 'from-pink-500/20 to-purple-500/20', text: 'text-pink-400', border: 'border-pink-500/40', badge: 'Meta' },
  { id: 'Facebook', name: 'Facebook', icon: FacebookIcon, color: 'from-blue-600/20 to-indigo-600/20', text: 'text-blue-400', border: 'border-blue-500/40', badge: 'Meta' },
  { id: 'X', name: 'X (Twitter)', icon: XIcon, color: 'from-slate-700/30 to-slate-800/30', text: 'text-white', border: 'border-slate-500/40', badge: 'v2 API' },
  { id: 'LinkedIn', name: 'LinkedIn', icon: LinkedInIcon, color: 'from-sky-600/20 to-blue-600/20', text: 'text-sky-400', border: 'border-sky-500/40', badge: 'Org API' }
];

export default function PlatformSelector({ selectedPlatform, onSelectPlatform, includeAll = false }) {
  const options = includeAll ? [{ id: 'ALL', name: 'All Platforms', icon: null, text: 'text-cyan-400', badge: 'Omnichannel' }, ...PLATFORMS_CONFIG] : PLATFORMS_CONFIG;

  return (
    <div className="flex flex-wrap gap-2.5">
      {options.map((p) => {
        const isSelected = selectedPlatform === p.id;
        const Icon = p.icon;
        return (
          <button
            key={p.id}
            type="button"
            onClick={() => onSelectPlatform(p.id)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all duration-200 active:scale-95 ${
              isSelected
                ? `bg-slate-900 ${p.border || 'border-cyan-500'} ${p.text} shadow-md shadow-cyan-500/10 ring-1 ring-cyan-500/30`
                : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            {Icon && <Icon className={`w-4 h-4 ${isSelected ? p.text : 'text-slate-400'}`} />}
            <span>{p.name}</span>
            {p.badge && (
              <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded ${isSelected ? 'bg-slate-800 text-cyan-300' : 'bg-slate-800/80 text-slate-500'}`}>
                {p.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
