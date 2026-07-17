'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useEffect } from 'react';

export default function LandingPage() {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user) router.push('/dashboard');
  }, [user, router]);

  const features = [
    { icon: '🧠', title: 'Smart Skill Gap Analysis', desc: 'Compare your profile against company requirements. Get prioritized action plans instantly.', gradient: 'from-violet-600 to-purple-500' },
    { icon: '🗺️', title: 'Personalized Roadmaps', desc: 'Week-by-week preparation plans tailored to your branch, CGPA, and target company.', gradient: 'from-cyan-600 to-sky-500' },
    { icon: '🎤', title: 'Mock Interviews', desc: 'HR, Technical, DSA, Core CS, and Behavioral interviews with detailed scoring and feedback.', gradient: 'from-emerald-600 to-green-500' },
    { icon: '📄', title: 'Resume ATS Analysis', desc: 'Upload your resume and get an ATS score, improvement suggestions, and keyword recommendations.', gradient: 'from-amber-600 to-yellow-500' },
    { icon: '📚', title: 'Learning Resources', desc: 'Curated videos, articles, and practice sheets matched to your current roadmap week.', gradient: 'from-red-600 to-rose-500' },
    { icon: '🔔', title: 'Smart Notifications', desc: 'Never miss a placement deadline, assessment, or roadmap milestone.', gradient: 'from-violet-600 to-cyan-500' },
  ];

  const steps = [
    { num: '01', title: 'Create your profile', desc: 'Enter your branch, CGPA, skills, and target companies.' },
    { num: '02', title: 'Upload your resume', desc: 'AI analyzes it for ATS compatibility and improvement areas.' },
    { num: '03', title: 'Get your roadmap', desc: 'Receive a personalized week-by-week preparation plan.' },
    { num: '04', title: 'Practice & improve', desc: 'Mock interviews, learning resources, and progress tracking.' },
  ];

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      {/* Navbar */}
      <nav className="sticky top-0 z-50 flex items-center justify-between px-12 py-4 border-b backdrop-blur-xl"
        style={{ background: 'rgba(10,13,20,0.85)', borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-2 text-lg font-bold">
          <span>🎓</span>
          <span>PlaceMentor <span className="text-purple-400">AI</span></span>
        </div>
        <div className="flex items-center gap-6">
          <a href="#features" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">Features</a>
          <a href="#how-it-works" className="text-sm font-medium text-slate-400 hover:text-white transition-colors">How it works</a>
          <Link href="/login">
            <button className="px-4 py-2 text-sm font-semibold border rounded-lg transition-all hover:border-purple-400 hover:text-purple-400"
              style={{ borderColor: 'var(--border2)', color: 'var(--text)' }}>
              Login
            </button>
          </Link>
          <Link href="/register">
            <button className="px-4 py-2 text-sm font-semibold text-white rounded-lg transition-all hover:opacity-90"
              style={{ background: 'linear-gradient(135deg,#7c3aed,#a855f7)' }}>
              Get Started
            </button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative flex items-center justify-between min-h-[calc(100vh-65px)] px-12 py-20 gap-16 overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse 600px 400px at 20% 50%,rgba(124,58,237,0.12),transparent 70%),radial-gradient(ellipse 500px 350px at 80% 30%,rgba(6,182,212,0.08),transparent 70%)' }} />

        {/* Left */}
        <div className="relative z-10 flex-1 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-medium text-purple-400 mb-6 border"
            style={{ background: 'rgba(124,58,237,0.12)', borderColor: 'rgba(124,58,237,0.3)' }}>
            🚀 Powered by Groq + LangGraph
          </div>
          <h1 className="text-6xl font-black leading-[1.1] mb-5 tracking-tight">
            Your AI-Powered<br />
            <span className="gradient-text">Placement Mentor</span>
          </h1>
          <p className="text-lg text-slate-400 mb-10 leading-relaxed">
            Personalized roadmaps. Smart mock interviews. Resume analysis.<br />
            Everything you need to land your dream placement at LPU.
          </p>
          <div className="flex gap-4 mb-12">
            <Link href="/register">
              <button className="px-8 py-3.5 text-base font-semibold text-white rounded-xl transition-all hover:opacity-90 hover:-translate-y-0.5 hover:shadow-xl"
                style={{ background: 'linear-gradient(135deg,#7c3aed,#a855f7)', boxShadow: '0 4px 20px rgba(124,58,237,0.3)' }}>
                Start Your Journey →
              </button>
            </Link>
            <Link href="/login">
              <button className="px-8 py-3.5 text-base font-medium text-slate-400 rounded-xl transition-all hover:text-white">
                Already have an account
              </button>
            </Link>
          </div>
          <div className="flex gap-10">
            {[['10+','AI Agents'],['RAG','Knowledge Base'],['∞','Mock Interviews'],['24/7','Always Available']].map(([num, label]) => (
              <div key={label} className="text-center">
                <div className="text-2xl font-black gradient-text">{num}</div>
                <div className="text-xs text-slate-500 font-medium mt-1">{label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right — Chat preview */}
        <div className="relative z-10 flex-shrink-0 w-96">
          <div className="rounded-2xl p-5 border shadow-2xl" style={{ background: 'var(--bg3)', borderColor: 'var(--border2)', boxShadow: '0 8px 48px rgba(0,0,0,0.6),0 0 60px rgba(124,58,237,0.1)' }}>
            <div className="flex items-center gap-2.5 mb-4 text-sm font-semibold text-slate-400">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              PlaceMentor AI
            </div>
            <div className="p-3 rounded-xl text-sm leading-relaxed text-slate-200 mb-3 border" style={{ background: 'var(--bg2)', borderColor: 'var(--border)', borderRadius: '4px 14px 14px 14px' }}>
              👋 Hi Rahul! Based on your profile, I&apos;ve identified 3 critical skill gaps for your Amazon SDE target. Want me to generate your 8-week roadmap?
            </div>
            <div className="p-3 rounded-xl text-sm text-white ml-auto max-w-[85%] mb-3" style={{ background: 'linear-gradient(135deg,#7c3aed,#a855f7)', borderRadius: '14px 4px 14px 14px' }}>
              Yes, please! Also can you review my resume?
            </div>
            <div className="flex gap-1.5 p-3 w-16" style={{ background: 'var(--bg2)', borderRadius: '4px 14px 14px 14px', border: '1px solid var(--border)' }}>
              <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-12 py-24" style={{ background: 'var(--bg)' }}>
        <h2 className="text-4xl font-black text-center mb-3 tracking-tight">Everything you need to get placed</h2>
        <p className="text-center text-slate-400 mb-16">A complete AI-powered placement ecosystem</p>
        <div className="grid grid-cols-3 gap-5 max-w-6xl mx-auto">
          {features.map((f) => (
            <div key={f.title} className="p-7 rounded-2xl border transition-all hover:-translate-y-1 hover:shadow-2xl"
              style={{ background: 'var(--bg3)', borderColor: 'var(--border)' }}>
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.gradient} flex items-center justify-center text-2xl mb-4`}>{f.icon}</div>
              <h3 className="font-bold mb-2">{f.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="px-12 py-24" style={{ background: 'var(--bg2)' }}>
        <h2 className="text-4xl font-black text-center mb-16 tracking-tight">How it works</h2>
        <div className="flex items-center justify-center gap-4 max-w-4xl mx-auto flex-wrap">
          {steps.map((step, i) => (
            <div key={step.num} className="flex items-center gap-4">
              <div className="p-7 rounded-2xl border text-center w-48 flex-shrink-0" style={{ background: 'var(--bg3)', borderColor: 'var(--border)' }}>
                <div className="text-4xl font-black gradient-text mb-3">{step.num}</div>
                <h3 className="font-bold text-sm mb-2">{step.title}</h3>
                <p className="text-xs text-slate-400">{step.desc}</p>
              </div>
              {i < steps.length - 1 && <span className="text-2xl text-slate-600 flex-shrink-0">→</span>}
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="py-10 text-center text-sm text-slate-600 border-t" style={{ borderColor: 'var(--border)' }}>
        🎓 PlaceMentor AI — Built for LPU students. Powered by Groq + LangGraph + RAG.
      </footer>
    </div>
  );
}
