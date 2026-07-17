'use client';

import { useState, useEffect, useRef } from 'react';
import { ChatAPI, StudentAPI, MockInterview } from '@/lib/api';

// ─── Interview Types ──────────────────────────────────────────────────────────

const INTERVIEW_TYPES = [
  {
    id: 'technical',
    icon: '💻',
    title: 'Technical',
    desc: 'System design, coding, and architecture questions tailored to your target company.',
    accent: 'linear-gradient(135deg,#7c3aed,#6d28d9)',
    accentLight: 'rgba(124,58,237,0.12)',
    accentBorder: 'rgba(124,58,237,0.3)',
  },
  {
    id: 'dsa',
    icon: '🧩',
    title: 'DSA',
    desc: 'Data structures and algorithm challenges — arrays, trees, graphs, DP and more.',
    accent: 'linear-gradient(135deg,#0ea5e9,#0369a1)',
    accentLight: 'rgba(14,165,233,0.12)',
    accentBorder: 'rgba(14,165,233,0.3)',
  },
  {
    id: 'hr',
    icon: '🤝',
    title: 'HR Round',
    desc: 'Behavioral & culture-fit questions. Tell me about yourself, strengths, weaknesses.',
    accent: 'linear-gradient(135deg,#10b981,#059669)',
    accentLight: 'rgba(16,185,129,0.12)',
    accentBorder: 'rgba(16,185,129,0.3)',
  },
  {
    id: 'behavioral',
    icon: '🎯',
    title: 'Behavioral (STAR)',
    desc: 'Situation, Task, Action, Result structured answers for leadership & teamwork.',
    accent: 'linear-gradient(135deg,#f59e0b,#d97706)',
    accentLight: 'rgba(245,158,11,0.12)',
    accentBorder: 'rgba(245,158,11,0.3)',
  },
  {
    id: 'core_cs',
    icon: '🔬',
    title: 'Core CS',
    desc: 'OS, DBMS, Computer Networks, and OOP theory — fundamentals that matter.',
    accent: 'linear-gradient(135deg,#ec4899,#be185d)',
    accentLight: 'rgba(236,72,153,0.12)',
    accentBorder: 'rgba(236,72,153,0.3)',
  },
];

// ─── Types ────────────────────────────────────────────────────────────────────

interface ChatMsg {
  role: 'ai' | 'user';
  content: string;
}

// ─── Score Badge ──────────────────────────────────────────────────────────────

function ScoreBadge({ score }: { score?: number }) {
  if (score == null) return null;
  const color = score >= 7 ? '#10b981' : score >= 5 ? '#f59e0b' : '#ef4444';
  return (
    <span
      style={{
        background: `${color}20`,
        border: `1px solid ${color}50`,
        color,
        borderRadius: 20,
        padding: '2px 10px',
        fontSize: 12,
        fontWeight: 700,
      }}
    >
      {score.toFixed(1)}/10
    </span>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function InterviewPage() {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [phase, setPhase] = useState<'setup' | 'session'>('setup');
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [questionCount, setQuestionCount] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [company, setCompany] = useState('');
  const [answerInput, setAnswerInput] = useState('');
  const [isEnded, setIsEnded] = useState(false);
  const [history, setHistory] = useState<MockInterview[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const sessionId = useRef(crypto.randomUUID());
  const bottomRef = useRef<HTMLDivElement>(null);

  // Load history
  useEffect(() => {
    StudentAPI.getInterviews()
      .then((r) => setHistory(r.interviews ?? []))
      .catch(() => setHistory([]))
      .finally(() => setHistoryLoading(false));
  }, []);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function startInterview() {
    if (!selectedType) return;
    setPhase('session');
    setMessages([]);
    setQuestionCount(0);
    setIsEnded(false);
    setIsLoading(true);

    const typeLabel = INTERVIEW_TYPES.find((t) => t.id === selectedType)?.title ?? selectedType;
    const msg = `Start a ${typeLabel} mock interview${company ? ` for ${company}` : ''}`;

    try {
      const res = await ChatAPI.sendMessage(msg, {
        interview_action: 'start',
        interview_type: selectedType,
        target_company: company || undefined,
        session_id: sessionId.current,
      });
      setMessages([{ role: 'ai', content: res.response }]);
      setQuestionCount(1);
    } catch (e) {
      setMessages([{ role: 'ai', content: `Failed to start interview: ${(e as Error).message}` }]);
    } finally {
      setIsLoading(false);
    }
  }

  async function submitAnswer() {
    const trimmed = answerInput.trim();
    if (!trimmed || isLoading) return;
    setAnswerInput('');
    setMessages((prev) => [...prev, { role: 'user', content: trimmed }]);
    setIsLoading(true);

    try {
      const res = await ChatAPI.sendMessage(trimmed, {
        interview_action: 'answer',
        interview_type: selectedType,
        session_id: sessionId.current,
      });
      setMessages((prev) => [...prev, { role: 'ai', content: res.response }]);

      const isOver = /interview complete|final evaluation/i.test(res.response);
      if (isOver) setIsEnded(true);
      else setQuestionCount((c) => c + 1);
    } catch (e) {
      setMessages((prev) => [...prev, { role: 'ai', content: `Error: ${(e as Error).message}` }]);
    } finally {
      setIsLoading(false);
    }
  }

  function endInterview() {
    setPhase('setup');
    setMessages([]);
    setSelectedType(null);
    setCompany('');
    setIsEnded(false);
    sessionId.current = crypto.randomUUID();
  }

  const typeInfo = INTERVIEW_TYPES.find((t) => t.id === selectedType);

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '32px 24px', color: 'var(--text)' }}>
      <style>{`
        .type-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
        .answer-input:focus { outline: none; border-color: #7c3aed !important; box-shadow: 0 0 0 3px rgba(124,58,237,0.2); }
        .history-card:hover { border-color: var(--border2) !important; }
      `}</style>

      {/* ── SETUP PHASE ── */}
      {phase === 'setup' && (
        <>
          <div style={{ marginBottom: 28 }}>
            <h1 style={{ fontSize: 22, fontWeight: 800, margin: '0 0 6px' }}>🎤 Mock Interview</h1>
            <p style={{ color: 'var(--text-2)', fontSize: 14, margin: 0 }}>
              Choose your interview type, set a target company, and practice with our AI interviewer.
            </p>
          </div>

          {/* Type cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 14, marginBottom: 24 }}>
            {INTERVIEW_TYPES.map((type) => {
              const selected = selectedType === type.id;
              return (
                <button
                  key={type.id}
                  onClick={() => setSelectedType(type.id)}
                  className="type-card"
                  style={{
                    background: selected ? type.accentLight : 'var(--bg2)',
                    border: `2px solid ${selected ? type.accentBorder.replace('0.3', '0.7') : 'var(--border)'}`,
                    borderRadius: 14,
                    padding: '18px 18px',
                    textAlign: 'left',
                    cursor: 'pointer',
                    color: 'var(--text)',
                    transition: 'transform 0.2s, box-shadow 0.2s, background 0.2s, border-color 0.2s',
                  }}
                >
                  <div style={{ fontSize: 28, marginBottom: 10 }}>{type.icon}</div>
                  <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
                    {type.title}
                    {selected && (
                      <span style={{ background: type.accent, color: '#fff', borderRadius: 20, padding: '1px 8px', fontSize: 10 }}>✓</span>
                    )}
                  </div>
                  <div style={{ color: 'var(--text-2)', fontSize: 12, lineHeight: 1.5 }}>{type.desc}</div>
                </button>
              );
            })}
          </div>

          {/* Company input + Start */}
          <div
            style={{
              background: 'var(--bg2)',
              border: '1px solid var(--border)',
              borderRadius: 14,
              padding: '20px 24px',
              display: 'flex',
              gap: 14,
              alignItems: 'flex-end',
              flexWrap: 'wrap',
              marginBottom: 32,
            }}
          >
            <div style={{ flex: 1, minWidth: 180 }}>
              <label style={{ color: 'var(--text-2)', fontSize: 12, fontWeight: 600, display: 'block', marginBottom: 8 }}>
                TARGET COMPANY (optional)
              </label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Google, Microsoft, Infosys…"
                style={{
                  width: '100%',
                  background: 'var(--bg3)',
                  border: '1px solid var(--border2)',
                  borderRadius: 10,
                  padding: '10px 14px',
                  color: 'var(--text)',
                  fontSize: 14,
                  boxSizing: 'border-box',
                  transition: 'border-color 0.2s',
                }}
                className="answer-input"
              />
            </div>
            <button
              onClick={startInterview}
              disabled={!selectedType}
              style={{
                background: selectedType ? 'linear-gradient(135deg,#7c3aed,#a855f7)' : 'var(--bg3)',
                border: `1px solid ${selectedType ? 'transparent' : 'var(--border2)'}`,
                borderRadius: 10,
                padding: '11px 24px',
                color: selectedType ? '#fff' : 'var(--text-2)',
                fontSize: 14,
                fontWeight: 700,
                cursor: selectedType ? 'pointer' : 'not-allowed',
                transition: 'background 0.2s, color 0.2s',
                flexShrink: 0,
              }}
            >
              🚀 Start Interview
            </button>
          </div>

          {/* History */}
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: '0 0 14px' }}>📋 Past Interviews</h2>
            {historyLoading ? (
              <div style={{ color: 'var(--text-2)', fontSize: 14 }}>Loading history…</div>
            ) : history.length === 0 ? (
              <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 12, padding: '24px', textAlign: 'center', color: 'var(--text-2)', fontSize: 14 }}>
                No past interviews yet. Start your first one above!
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {history.map((iv) => {
                  const typeData = INTERVIEW_TYPES.find((t) => t.id === iv.interview_type);
                  return (
                    <div
                      key={iv.id}
                      className="history-card"
                      style={{
                        background: 'var(--bg2)',
                        border: '1px solid var(--border)',
                        borderRadius: 12,
                        padding: '14px 18px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 14,
                        transition: 'border-color 0.2s',
                      }}
                    >
                      <div style={{ fontSize: 24, flexShrink: 0 }}>{typeData?.icon ?? '🎤'}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 14, fontWeight: 600 }}>{typeData?.title ?? iv.interview_type}</div>
                        <div style={{ color: 'var(--text-2)', fontSize: 12, marginTop: 2 }}>
                          {iv.target_company ?? 'No company'} · {new Date(iv.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <ScoreBadge score={iv.overall_score} />
                        <span
                          style={{
                            background: iv.status === 'completed' ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)',
                            border: `1px solid ${iv.status === 'completed' ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'}`,
                            color: iv.status === 'completed' ? '#6ee7b7' : '#fcd34d',
                            borderRadius: 20,
                            padding: '2px 10px',
                            fontSize: 11,
                            fontWeight: 600,
                            textTransform: 'capitalize',
                          }}
                        >
                          {iv.status}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}

      {/* ── SESSION PHASE ── */}
      {phase === 'session' && (
        <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
          {/* Top bar */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              marginBottom: 16,
              flexShrink: 0,
              flexWrap: 'wrap',
            }}
          >
            <h1 style={{ fontSize: 18, fontWeight: 800, margin: 0 }}>Live Interview</h1>
            {typeInfo && (
              <span style={{ background: typeInfo.accentLight, border: `1px solid ${typeInfo.accentBorder}`, color: 'var(--text)', borderRadius: 20, padding: '4px 12px', fontSize: 12, fontWeight: 600 }}>
                {typeInfo.icon} {typeInfo.title}
              </span>
            )}
            {company && (
              <span style={{ background: 'var(--bg3)', border: '1px solid var(--border2)', borderRadius: 20, padding: '4px 12px', fontSize: 12 }}>
                🏢 {company}
              </span>
            )}
            <span style={{ background: 'var(--bg3)', border: '1px solid var(--border2)', borderRadius: 20, padding: '4px 12px', fontSize: 12 }}>
              Q{questionCount}
            </span>
            <button
              onClick={endInterview}
              style={{
                marginLeft: 'auto',
                background: 'rgba(239,68,68,0.1)',
                border: '1px solid rgba(239,68,68,0.3)',
                borderRadius: 10,
                padding: '8px 16px',
                color: '#fca5a5',
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              End Interview
            </button>
          </div>

          {/* Messages */}
          <div
            style={{
              flex: 1,
              overflowY: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 14,
              background: 'var(--bg2)',
              border: '1px solid var(--border)',
              borderRadius: 14,
              padding: 20,
              marginBottom: 16,
              scrollbarWidth: 'thin',
              scrollbarColor: 'var(--border2) transparent',
            }}
          >
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  flexDirection: msg.role === 'ai' ? 'row' : 'row-reverse',
                  gap: 10,
                  alignItems: 'flex-start',
                }}
              >
                <div
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: '50%',
                    background: msg.role === 'ai' ? 'linear-gradient(135deg,#7c3aed,#a855f7)' : 'linear-gradient(135deg,#374151,#4b5563)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 16,
                    flexShrink: 0,
                    marginTop: 2,
                  }}
                >
                  {msg.role === 'ai' ? '🎤' : '👤'}
                </div>
                <div
                  style={{
                    maxWidth: '75%',
                    background: msg.role === 'ai'
                      ? (isEnded && i === messages.length - 1 ? 'rgba(16,185,129,0.08)' : 'var(--bg3)')
                      : 'linear-gradient(135deg,#7c3aed,#6d28d9)',
                    border: `1px solid ${msg.role === 'ai' ? (isEnded && i === messages.length - 1 ? 'rgba(16,185,129,0.3)' : 'var(--border2)') : 'transparent'}`,
                    borderRadius: msg.role === 'ai' ? '4px 14px 14px 14px' : '14px 4px 14px 14px',
                    padding: '12px 16px',
                    color: 'var(--text)',
                    fontSize: 14,
                    lineHeight: 1.65,
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                <div style={{ width: 34, height: 34, borderRadius: '50%', background: 'linear-gradient(135deg,#7c3aed,#a855f7)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16 }}>🎤</div>
                <div style={{ background: 'var(--bg3)', border: '1px solid var(--border2)', borderRadius: '4px 14px 14px 14px', padding: '12px 16px', display: 'flex', gap: 4, alignItems: 'center' }}>
                  {[0, 1, 2].map((i) => (
                    <div key={i} style={{ width: 6, height: 6, borderRadius: '50%', background: '#a78bfa', animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          {!isEnded ? (
            <div style={{ display: 'flex', gap: 10, flexShrink: 0, marginBottom: 8 }}>
              <textarea
                value={answerInput}
                onChange={(e) => setAnswerInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitAnswer(); } }}
                placeholder="Type your answer… (Enter to submit)"
                rows={2}
                className="answer-input"
                style={{
                  flex: 1,
                  background: 'var(--bg2)',
                  border: '1px solid var(--border2)',
                  borderRadius: 12,
                  padding: '12px 16px',
                  color: 'var(--text)',
                  fontSize: 14,
                  resize: 'none',
                  fontFamily: 'inherit',
                  lineHeight: 1.5,
                  transition: 'border-color 0.2s, box-shadow 0.2s',
                }}
              />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <button
                  onClick={submitAnswer}
                  disabled={!answerInput.trim() || isLoading}
                  style={{
                    flex: 1,
                    background: 'linear-gradient(135deg,#7c3aed,#a855f7)',
                    border: 'none',
                    borderRadius: 10,
                    padding: '0 20px',
                    color: '#fff',
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: !answerInput.trim() || isLoading ? 'not-allowed' : 'pointer',
                    opacity: !answerInput.trim() || isLoading ? 0.6 : 1,
                    transition: 'opacity 0.2s',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Submit →
                </button>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '12px 0', flexShrink: 0 }}>
              <div style={{ color: '#6ee7b7', fontSize: 14, fontWeight: 600, marginBottom: 10 }}>
                ✅ Interview Complete! Check the evaluation above.
              </div>
              <button
                onClick={endInterview}
                style={{
                  background: 'linear-gradient(135deg,#7c3aed,#a855f7)',
                  border: 'none',
                  borderRadius: 10,
                  padding: '11px 28px',
                  color: '#fff',
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Start New Interview
              </button>
            </div>
          )}
        </div>
      )}

      <style>{`
        @keyframes bounce {
          0%,80%,100% { transform: translateY(0); opacity: 0.5; }
          40% { transform: translateY(-6px); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
