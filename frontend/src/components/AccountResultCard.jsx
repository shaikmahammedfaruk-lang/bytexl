import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  ExternalLink,
  Users,
  Calendar,
  Globe,
  Mail,
  Phone,
  ShieldCheck,
  ShieldAlert,
  Info,
  Clock,
  Layers
} from 'lucide-react';
import { InstagramIcon, FacebookIcon, XIcon, LinkedInIcon } from './PlatformSelector';

export default function AccountResultCard({ profile, identityConsistency, timestamp }) {
  if (!profile) return null;

  const getPlatformIcon = (plat) => {
    switch (plat) {
      case 'Instagram':
        return <InstagramIcon className="w-5 h-5 text-pink-400" />;
      case 'Facebook':
        return <FacebookIcon className="w-5 h-5 text-blue-400" />;
      case 'X':
        return <XIcon className="w-5 h-5 text-white" />;
      case 'LinkedIn':
        return <LinkedInIcon className="w-5 h-5 text-sky-400" />;
      default:
        return <Globe className="w-5 h-5 text-cyan-400" />;
    }
  };

  const isVerified = profile.official_platform_verification === 'Verified';
  const isUnknown = profile.official_platform_verification === 'Unknown';

  return (
    <div className="p-5 rounded-2xl bg-[#0b101e] border border-slate-800 shadow-xl space-y-4">
      {/* Top Banner: Profile Identity & Platform Badge */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div className="flex items-center gap-3.5">
          {profile.avatar_url ? (
            <img
              src={profile.avatar_url}
              alt={profile.display_name}
              className="w-14 h-14 rounded-2xl object-cover border-2 border-slate-700 bg-slate-900 p-0.5"
              onError={(e) => { e.target.style.display = 'none'; }}
            />
          ) : (
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 flex items-center justify-center text-slate-300 font-bold text-lg">
              {profile.display_name ? profile.display_name[0] : '@'}
            </div>
          )}

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-bold text-white">{profile.display_name}</h3>
              {/* Platform Official Badge Pill */}
              <span
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 border ${
                  isVerified
                    ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                    : isUnknown
                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}
              >
                {isVerified ? (
                  <>
                    <CheckCircle2 className="w-3 h-3 text-blue-400" />
                    <span>Official {profile.platform} Badge</span>
                  </>
                ) : isUnknown ? (
                  <>
                    <HelpCircle className="w-3 h-3 text-amber-400" />
                    <span>Verification Unknown</span>
                  </>
                ) : (
                  <span>Unverified on {profile.platform}</span>
                )}
              </span>
            </div>

            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs font-mono text-cyan-400 font-semibold">{profile.username}</span>
              <span className="text-slate-600">•</span>
              <span className="text-xs text-slate-400 flex items-center gap-1">
                {getPlatformIcon(profile.platform)}
                {profile.platform}
              </span>
              {profile.page_category && (
                <>
                  <span className="text-slate-600">•</span>
                  <span className="text-[11px] text-slate-400 px-2 py-0.2 rounded bg-slate-900 border border-slate-800">
                    {profile.page_category}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Visit External Link Button */}
        {profile.profile_url && (
          <a
            href={profile.profile_url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/80 text-xs font-semibold flex items-center gap-1.5 transition active:scale-95 whitespace-nowrap self-start md:self-auto"
          >
            <span>Open {profile.platform} Profile</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>

      {/* Critical Verification Distinction Disclaimer */}
      <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-[11px] text-slate-400 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-200">Official Platform Badge vs BrandShield Authenticity Assessment:</strong>
          <p className="mt-0.5 text-slate-400 leading-relaxed">
            The badge above reflects the platform's native status ({profile.verification_badge_type || profile.official_platform_verification}).
            BrandShield AI independently verifies whether this profile belongs to your registered protected brand baseline.
            Unverified status alone is never treated as evidence that an account is fraudulent.
          </p>
        </div>
      </div>

      {/* Profile Bio & Telemetry Grid */}
      {profile.bio && (
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
            Profile Biography / About:
          </span>
          <p className="text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
            {profile.bio}
          </p>
        </div>
      )}

      {/* Numerical Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
        <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-400 block">Followers</span>
          <span className="text-base font-bold text-white mt-0.5 block font-mono">
            {profile.followers_count !== undefined ? Number(profile.followers_count).toLocaleString() : 'N/A'}
          </span>
          <span className="text-[10px] text-slate-500">Audience Reach</span>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-400 block">Following</span>
          <span className="text-base font-bold text-white mt-0.5 block font-mono">
            {profile.following_count !== undefined ? Number(profile.following_count).toLocaleString() : 'N/A'}
          </span>
          <span className="text-[10px] text-slate-500">Accounts Followed</span>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-400 block">Posts / Media</span>
          <span className="text-base font-bold text-white mt-0.5 block font-mono">
            {profile.media_or_posts_count !== undefined ? Number(profile.media_or_posts_count).toLocaleString() : 'N/A'}
          </span>
          <span className="text-[10px] text-slate-500">Published Content</span>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-400 block">Account Age</span>
          <span className="text-base font-bold text-white mt-0.5 block font-mono truncate">
            {profile.account_created_date || 'Established'}
          </span>
          <span className="text-[10px] text-slate-500">Registration Date</span>
        </div>
      </div>

      {/* Identity Consistency Indicators */}
      {identityConsistency && (
        <div className="space-y-2 pt-2 border-t border-slate-800">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
            Account Identity Consistency Indicators:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <div className={`p-2.5 rounded-lg border flex items-center justify-between ${
              identityConsistency.exact_name_match
                ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
                : 'bg-slate-900 border-slate-800 text-slate-300'
            }`}>
              <span>Exact Brand Name Match</span>
              <span className="font-bold">{identityConsistency.exact_name_match ? 'YES' : 'NO'}</span>
            </div>

            <div className={`p-2.5 rounded-lg border flex items-center justify-between ${
              identityConsistency.lookalike_detected
                ? 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                : 'bg-slate-900 border-slate-800 text-slate-300'
            }`}>
              <span>Look-alike Discrepancy</span>
              <span className="font-bold">{identityConsistency.lookalike_detected ? 'DETECTED' : 'CLEAR'}</span>
            </div>

            <div className={`p-2.5 rounded-lg border flex items-center justify-between ${
              identityConsistency.official_registry_mismatch
                ? 'bg-amber-950/20 border-amber-500/30 text-amber-300'
                : 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
            }`}>
              <span>Official Registry Match</span>
              <span className="font-bold">{identityConsistency.official_registry_mismatch ? 'NOT REGISTERED' : 'VERIFIED BASELINE'}</span>
            </div>

            <div className={`p-2.5 rounded-lg border flex items-center justify-between ${
              identityConsistency.suspicious_contact_patterns
                ? 'bg-rose-950/20 border-rose-500/30 text-rose-300'
                : 'bg-slate-900 border-slate-800 text-slate-300'
            }`}>
              <span>Suspicious Contact / Helpdesk Flags</span>
              <span className="font-bold">{identityConsistency.suspicious_contact_patterns ? 'FLAGGED' : 'CLEAR'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Provenance & API Limits Footer */}
      <div className="pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between text-[10px] text-slate-500 gap-2">
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>Scanned: {timestamp ? new Date(timestamp).toLocaleString() : 'Just now'}</span>
          <span className="text-slate-700">|</span>
          <span className="text-slate-400">Data Source: {profile.data_source}</span>
        </div>

        {profile.api_limitations_notice && (
          <span className="text-slate-400 italic">
            * {profile.api_limitations_notice}
          </span>
        )}
      </div>
    </div>
  );
}
