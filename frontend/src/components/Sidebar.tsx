'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';

const NAV = [
  { href: '/dashboard',           icon: '📊', label: 'Dashboard' },
  { href: '/dashboard/chat',      icon: '💬', label: 'AI Mentor Chat' },
  { href: '/dashboard/roadmap',   icon: '🗺️', label: 'My Roadmap' },
  { href: '/dashboard/interview', icon: '🎤', label: 'Mock Interview' },
  { href: '/dashboard/resume',    icon: '📄', label: 'Resume' },
  { href: '/dashboard/profile',   icon: '👤', label: 'My Profile' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const initial = user?.full_name?.[0]?.toUpperCase() ?? 'S';
  const firstName = user?.full_name?.split(' ')[0] ?? 'Student';

  return (
    <aside className="w-60 flex-shrink-0 flex flex-col h-screen sticky top-0 border-r"
      style={{ background: 'var(--bg2)', borderColor: 'var(--border)' }}>
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-5 py-6 text-base font-bold border-b" style={{ borderColor: 'var(--border)' }}>
        <span className="text-xl">🎓</span>
        <span>PlaceMentor <span className="text-purple-400">AI</span></span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
        {NAV.map(({ href, icon, label }) => {
          const active = pathname === href;
          return (
            <Link key={href} href={href}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                active
                  ? 'text-purple-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
              }`}
              style={active ? { background: 'rgba(124,58,237,0.15)' } : {}}>
              <span className="text-base w-5">{icon}</span>
              {label}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="p-4 border-t space-y-2.5" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 text-white"
            style={{ background: 'linear-gradient(135deg,#7c3aed,#06b6d4)' }}>
            {initial}
          </div>
          <div>
            <div className="text-sm font-semibold">{firstName}</div>
            <div className="text-xs text-slate-500">Student</div>
          </div>
        </div>
        <button onClick={logout}
          className="w-full text-xs py-1.5 rounded-lg border transition-all text-slate-500 hover:text-red-400 hover:border-red-500/40"
          style={{ borderColor: 'var(--border)' }}>
          ↩ Logout
        </button>
      </div>
    </aside>
  );
}
