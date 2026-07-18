'use client';

import { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import {
  StudentAPI,
  ResumeAPI,
  ChatAPI,
  StudentProfile,
  Roadmap,
  Resume,
  MockInterview,
} from '@/lib/api';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}

// ─── Stat Card ────────────────────────────────────────────────────────────────

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  gradient: string;
  icon: React.ReactNode;
}

function StatCard({ label, value, sub, gradient, icon }: StatCardProps) {
  return (
    <div
      style={{
        background: 'var(--bg2)',
        border: '1px solid var(--border)',
        borderRadius: 16,
        padding: '20px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        position: 'relative',
        overflow: 'hidden',
        transition: 'transform 0.2s, box-shadow 0.2s',
      }}
      className="stat-card hover:scale-[1.02] hover:shadow-2xl"
    >
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: 12,
          background: gradient,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 22,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div>
        <div style={{ color: 'var(--text-2)', fontSize: 13, fontWeight: 500, marginBottom: 4 }}>
          {label}
        </div>
        <div style={{ color: 'var(--text)', fontSize: 28, fontWeight: 700, letterSpacing: -0.5 }}>
          {value}
        </div>
        {sub && (
          <div style={{ color: 'var(--text-2)', fontSize: 12, marginTop: 4 }}>{sub}</div>
        )}
      </div>
      {/* Glow accent */}
      <div
        style={{
          position: 'absolute',
          top: -30,
          right: -30,
          width: 100,
          height: 100,
          borderRadius: '50%',
          background: gradient,
          opacity: 0.08,
          filter: 'blur(20px)',
          pointerEvents: 'none',
        }}
      />
    </div>
  );
}

// ─── Quick Action Button ───────────────────────────────────────────────────────

interface QuickActionProps {
  href: string;
  icon: string;
  label: string;
  desc: string;
  accent: string;
}

function QuickAction({ href, icon, label, desc, accent }: QuickActionProps) {
  return (
    <Link
      href={href}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '14px 16px',
        borderRadius: 12,
        border: '1px solid var(--border2)',
        background: 'var(--bg3)',
        textDecoration: 'none',
        transition: 'background 0.2s, border-color 0.2s, transform 0.15s',
      }}
      className="quick-action"
    >
      <div
        style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          background: accent,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 18,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div>
        <div style={{ color: 'var(--text)', fontSize: 14, fontWeight: 600 }}>{label}</div>
        <div style={{ color: 'var(--text-2)', fontSize: 12 }}>{desc}</div>
      </div>
      <span style={{ color: 'var(--text-2)', marginLeft: 'auto', fontSize: 16 }}>›</span>
    </Link>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [interviews, setInterviews] = useState<{ interviews: MockInterview[]; average_score?: number } | null>(null);
  const [activeResume, setActiveResume] = useState<Resume | null>(null);
  const [dataLoading, setDataLoading] = useState(true);

  // Quick AI ask
  const [question, setQuestion] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const sessionId = useRef(crypto.randomUUID());

  useEffect(() => {
    async function load() {
      const [profileRes, roadmapRes, interviewsRes, resumesRes] = await Promise.allSettled([
        StudentAPI.getProfile(),
        StudentAPI.getRoadmap(),
        StudentAPI.getInterviews(),
        ResumeAPI.list(),
      ]);
      if (profileRes.status === 'fulfilled') setProfile(profileRes.value.profile);
      if (roadmapRes.status === 'fulfilled') setRoadmap(roadmapRes.value);
      if (interviewsRes.status === 'fulfilled') setInterviews(interviewsRes.value);
      if (resumesRes.status === 'fulfilled') {
        const active = resumesRes.value.find((r) => r.is_active) ?? resumesRes.value[0] ?? null;
        setActiveResume(active);
      }
      setDataLoading(false);
    }
    load();
  }, []);

  async function askAI() {
    if (!question.trim() || aiLoading) return;
    setAiLoading(true);
    setAiResponse('');
    let streamed = '';
    let streamFailed = false;
    await ChatAPI.streamMessage(
      question,
      (chunk) => { streamed += chunk; setAiResponse(streamed); },
      undefined,
      () => { streamFailed = true; },
      sessionId.current,
    );
    if (streamFailed || !streamed) {
      try {
        const res = await ChatAPI.sendMessage(question, { session_id: sessionId.current });
        setAiResponse(res.response);
      } catch {
        setAiResponse('Sorry, I could not process your question right now.');
      }
    }
    setAiLoading(false);
  }

  const readinessScore = interviews?.average_score != null
    ? Math.round(Math.min(100, interviews.average_score * 10))
    : null;

  const roadmapProgress = roadmap?.current_week && roadmap?.duration_weeks
    ? `Week ${roadmap.current_week} / ${roadmap.duration_weeks}`
    : 'No roadmap';

  const interviewCount = interviews?.interviews?.length ?? 0;
  const atsScore = activeResume?.ats_score ?? null;

  const greeting = getGreeting();
  const name = user?.full_name?.split(' ')[0] ?? 'Student';

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px', color: 'var(--text)' }}>
      <style>{`
        .stat-card:hover { transform: translateY(-2px); box-shadow: 0 16px 48px rgba(0,0,0,0.4); }
        .quick-action:hover { background: var(--bg2) !important; border-color: #7c3aed !important; transform: translateX(2px); }
        .ai-ask-input:focus { outline: none; border-color: #7c3aed !important; box-shadow: 0 0 0 3px rgba(124,58,237,0.2); }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: 36 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              background: 'linear-gradient(135deg,#7c3aed,#a855f7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 20,
              fontWeight: 700,
              color: '#fff',
              flexShrink: 0,
            }}
          >
            {name[0]?.toUpperCase()}
          </div>
          <div>
            <div style={{ color: 'var(--text-2)', fontSize: 14 }}>{greeting} 👋</div>
            <h1 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text)', margin: 0, letterSpacing: -0.5 }}>
              Welcome back, <span style={{ background: 'linear-gradient(90deg,#a855f7,#7c3aed)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>{name}</span>
            </h1>
          </div>
        </div>
        <p style={{ color: 'var(--text-2)', fontSize: 14, margin: 0 }}>
          Here&apos;s your placement preparation snapshot for today.
        </p>
      </div>

      {/* Stat Cards */}
      {dataLoading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 16, marginBottom: 28 }}>
          {[0, 1, 2, 3].map((i) => (
            <div key={i} style={{ background: 'var(--bg2)', borderRadius: 16, height: 130, border: '1px solid var(--border)', animation: 'pulse 1.5s ease-in-out infinite' }} />
          ))}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 16, marginBottom: 28 }}>
          <StatCard
            label="Placement Readiness"
            value={readinessScore != null ? `${readinessScore}%` : '—'}
            sub="Based on interview scores"
            gradient="linear-gradient(135deg,#7c3aed,#6d28d9)"
            icon="🎯"
          />
          <StatCard
            label="Roadmap Progress"
            value={roadmap?.completion_pct != null ? `${Math.round(roadmap.completion_pct)}%` : '—'}
            sub={roadmapProgress}
            gradient="linear-gradient(135deg,#0ea5e9,#0369a1)"
            icon="🗺️"
          />
          <StatCard
            label="Mock Interviews"
            value={interviewCount}
            sub={interviews?.average_score != null ? `Avg score: ${interviews.average_score.toFixed(1)}/10` : 'No scores yet'}
            gradient="linear-gradient(135deg,#10b981,#059669)"
            icon="🎤"
          />
          <StatCard
            label="ATS Score"
            value={atsScore != null ? `${atsScore}/100` : '—'}
            sub={activeResume ? activeResume.original_name : 'No resume uploaded'}
            gradient="linear-gradient(135deg,#f59e0b,#d97706)"
            icon="📄"
          />
        </div>
      )}

      {/* Two-column grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }} className="two-col-grid">
        <style>{`
          @media (max-width: 700px) { .two-col-grid { grid-template-columns: 1fr !important; } }
        `}</style>

        {/* Quick Actions */}
        <div
          style={{
            background: 'var(--bg2)',
            border: '1px solid var(--border)',
            borderRadius: 16,
            padding: 24,
          }}
        >
          <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)', margin: '0 0 16px' }}>
            ⚡ Quick Actions
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <QuickAction href="/dashboard/chat" icon="🤖" label="AI Mentor Chat" desc="Ask anything about placements" accent="linear-gradient(135deg,#7c3aed,#a855f7)" />
            <QuickAction href="/dashboard/roadmap" icon="🗺️" label="My Roadmap" desc="View & track your prep plan" accent="linear-gradient(135deg,#0ea5e9,#0369a1)" />
            <QuickAction href="/dashboard/interview" icon="🎤" label="Mock Interview" desc="Practice with AI interviewer" accent="linear-gradient(135deg,#10b981,#059669)" />
            <QuickAction href="/dashboard/resume" icon="📄" label="Resume Analyzer" desc="Upload & get ATS feedback" accent="linear-gradient(135deg,#f59e0b,#d97706)" />
            <QuickAction href="/dashboard/profile" icon="👤" label="Edit Profile" desc="Update skills & preferences" accent="linear-gradient(135deg,#ec4899,#db2777)" />
            <QuickAction href="/dashboard/chat" icon="📚" label="AI Resources" desc="DSA sheets, guides & more" accent="linear-gradient(135deg,#6366f1,#4f46e5)" />
          </div>
        </div>

        {/* Profile Summary */}
        <div
          style={{
            background: 'var(--bg2)',
            border: '1px solid var(--border)',
            borderRadius: 16,
            padding: 24,
          }}
        >
          <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)', margin: '0 0 16px' }}>
            👤 Profile Summary
          </h2>
          {dataLoading ? (
            <div style={{ color: 'var(--text-2)', fontSize: 14 }}>Loading…</div>
          ) : !profile ? (
            <div style={{ textAlign: 'center', padding: '24px 0' }}>
              <div style={{ fontSize: 36, marginBottom: 8 }}>🔧</div>
              <div style={{ color: 'var(--text-2)', fontSize: 14, marginBottom: 16 }}>
                Complete your profile to unlock personalized insights
              </div>
              <Link
                href="/dashboard/profile"
                style={{
                  background: 'linear-gradient(135deg,#7c3aed,#a855f7)',
                  color: '#fff',
                  borderRadius: 10,
                  padding: '10px 20px',
                  fontSize: 13,
                  fontWeight: 600,
                  textDecoration: 'none',
                  display: 'inline-block',
                }}
              >
                Set Up Profile →
              </Link>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {[
                { label: 'Branch', value: profile.branch ?? '—' },
                { label: 'Semester', value: profile.semester ? `Semester ${profile.semester}` : '—' },
                { label: 'CGPA', value: profile.cgpa != null ? profile.cgpa.toFixed(2) : '—' },
              ].map(({ label, value }) => (
                <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ color: 'var(--text-2)', fontSize: 13 }}>{label}</span>
                  <span style={{ color: 'var(--text)', fontSize: 13, fontWeight: 600 }}>{value}</span>
                </div>
              ))}

              {profile.preferred_companies && profile.preferred_companies.length > 0 && (
                <div>
                  <div style={{ color: 'var(--text-2)', fontSize: 13, marginBottom: 6 }}>Target Companies</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {profile.preferred_companies.slice(0, 5).map((c) => (
                      <span key={c} style={{ background: 'rgba(124,58,237,0.15)', border: '1px solid rgba(124,58,237,0.3)', color: '#a78bfa', borderRadius: 20, padding: '2px 10px', fontSize: 12 }}>
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {profile.skills && profile.skills.length > 0 && (
                <div>
                  <div style={{ color: 'var(--text-2)', fontSize: 13, marginBottom: 6 }}>Top Skills</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {profile.skills.slice(0, 6).map((s) => (
                      <span key={s} style={{ background: 'var(--bg3)', border: '1px solid var(--border2)', color: 'var(--text)', borderRadius: 20, padding: '2px 10px', fontSize: 12 }}>
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {!profile.branch && !profile.skills?.length && (
                <div style={{ color: 'var(--text-2)', fontSize: 13 }}>
                  No profile data yet.{' '}
                  <Link href="/dashboard/profile" style={{ color: '#a78bfa', textDecoration: 'underline' }}>
                    Complete your profile →
                  </Link>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Quick AI Ask */}
      <div
        style={{
          background: 'var(--bg2)',
          border: '1px solid var(--border)',
          borderRadius: 16,
          padding: 24,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* bg glow */}
        <div
          style={{
            position: 'absolute',
            top: -60,
            right: -60,
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: 'linear-gradient(135deg,#7c3aed,#a855f7)',
            opacity: 0.06,
            filter: 'blur(40px)',
            pointerEvents: 'none',
          }}
        />
        <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)', margin: '0 0 6px' }}>
          🤖 Ask PlaceMentor AI
        </h2>
        <p style={{ color: 'var(--text-2)', fontSize: 13, margin: '0 0 16px' }}>
          Quick question? Type below and get an instant answer.
        </p>
        <div style={{ display: 'flex', gap: 10 }}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && askAI()}
            placeholder="e.g. What topics should I study for Google SDE-1?"
            className="ai-ask-input"
            style={{
              flex: 1,
              background: 'var(--bg3)',
              border: '1px solid var(--border2)',
              borderRadius: 10,
              padding: '11px 16px',
              color: 'var(--text)',
              fontSize: 14,
              transition: 'border-color 0.2s, box-shadow 0.2s',
            }}
          />
          <button
            onClick={askAI}
            disabled={aiLoading || !question.trim()}
            style={{
              background: 'linear-gradient(135deg,#7c3aed,#a855f7)',
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              padding: '11px 20px',
              fontSize: 14,
              fontWeight: 600,
              cursor: aiLoading || !question.trim() ? 'not-allowed' : 'pointer',
              opacity: aiLoading || !question.trim() ? 0.6 : 1,
              transition: 'opacity 0.2s',
              whiteSpace: 'nowrap',
            }}
          >
            {aiLoading ? '…' : 'Ask →'}
          </button>
        </div>

        {aiResponse && (
          <div
            style={{
              marginTop: 16,
              background: 'var(--bg3)',
              border: '1px solid var(--border2)',
              borderRadius: 12,
              padding: '14px 18px',
              color: 'var(--text)',
              fontSize: 14,
              lineHeight: 1.7,
              whiteSpace: 'pre-wrap',
            }}
          >
            <span style={{ color: '#a78bfa', fontWeight: 600, marginRight: 6 }}>🎓</span>
            {aiResponse}
            <div style={{ marginTop: 10 }}>
              <Link
                href="/dashboard/chat"
                style={{ color: '#a78bfa', fontSize: 12, textDecoration: 'underline' }}
              >
                Continue this conversation in full chat →
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
