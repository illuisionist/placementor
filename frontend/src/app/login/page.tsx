'use client';
import { useState, FormEvent } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AuthAPI } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await AuthAPI.login(email, password);
      login(res.access_token, res.user);
      router.push('/dashboard');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6"
      style={{ background: 'radial-gradient(ellipse 500px 400px at 30% 40%,rgba(124,58,237,0.1),transparent 70%),var(--bg)' }}>
      <div className="w-full max-w-md">
        <Link href="/" className="flex items-center justify-center gap-2 text-xl font-bold mb-10">
          🎓 PlaceMentor <span className="text-purple-400">AI</span>
        </Link>
        <div className="p-9 rounded-2xl border shadow-2xl" style={{ background: 'var(--bg3)', borderColor: 'var(--border2)' }}>
          <h2 className="text-2xl font-bold mb-1">Welcome back</h2>
          <p className="text-slate-400 text-sm mb-7">Sign in to continue your placement journey</p>

          {error && (
            <div className="p-3 rounded-lg text-sm text-red-300 mb-5 border" style={{ background: 'rgba(239,68,68,0.1)', borderColor: 'rgba(239,68,68,0.3)' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Email</label>
              <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
                placeholder="you@lpu.in"
                className="w-full px-4 py-2.5 rounded-lg text-sm outline-none transition-all focus:ring-2 focus:ring-purple-500/40"
                style={{ background: 'var(--bg2)', border: '1px solid var(--border2)', color: 'var(--text)' }} />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1.5">Password</label>
              <input type="password" required value={password} onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2.5 rounded-lg text-sm outline-none transition-all focus:ring-2 focus:ring-purple-500/40"
                style={{ background: 'var(--bg2)', border: '1px solid var(--border2)', color: 'var(--text)' }} />
            </div>
            <button type="submit" disabled={loading}
              className="w-full py-2.5 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ background: 'linear-gradient(135deg,#7c3aed,#a855f7)' }}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="text-center text-sm text-slate-500 mt-5">
            Don&apos;t have an account?{' '}
            <Link href="/register" className="text-purple-400 font-medium hover:underline">Register here</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
