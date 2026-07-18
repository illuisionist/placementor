'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { StudentAPI, Roadmap, RoadmapWeek } from '@/lib/api';

// ─── Circular Progress Ring ───────────────────────────────────────────────────

function ProgressRing({ pct, size = 100 }: { pct: number; size?: number }) {
  const r = (size - 12) / 2;
  const circ = 2 * Math.PI * r;
  const dash = circ * (pct / 100);
  return (
    <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border2)" strokeWidth={8} />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="url(#ringGrad)"
        strokeWidth={8}
        strokeLinecap="round"
        strokeDasharray={`${dash} ${circ}`}
        style={{ transition: 'stroke-dasharray 1s ease' }}
      />
      <defs>
        <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#7c3aed" />
          <stop offset="100%" stopColor="#a855f7" />
        </linearGradient>
      </defs>
    </svg>
  );
}

// ─── Week Card ────────────────────────────────────────────────────────────────

function WeekCard({
  week,
  isCurrent,
  isExpanded,
  onToggle,
  onToggleTask,
}: {
  week: RoadmapWeek;
  isCurrent: boolean;
  isExpanded: boolean;
  onToggle: () => void;
  onToggleTask?: (taskIndex: number, isCompleted: boolean) => void;
}) {
  return (
    <div
      style={{
        background: 'var(--bg2)',
        border: `1px solid ${isCurrent ? '#7c3aed' : 'var(--border)'}`,
        borderRadius: 14,
        overflow: 'hidden',
        transition: 'border-color 0.2s, box-shadow 0.2s',
        boxShadow: isCurrent ? '0 0 0 1px #7c3aed40, 0 4px 20px rgba(124,58,237,0.1)' : undefined,
      }}
    >
      {/* Header */}
      <button
        onClick={onToggle}
        style={{
          width: '100%',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          padding: '16px 20px',
          textAlign: 'left',
          color: 'var(--text)',
        }}
      >
        {/* Week badge */}
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: 10,
            background: isCurrent
              ? 'linear-gradient(135deg,#7c3aed,#a855f7)'
              : 'var(--bg3)',
            border: '1px solid var(--border2)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            fontSize: 10,
            fontWeight: 700,
            color: isCurrent ? '#fff' : 'var(--text-2)',
            lineHeight: 1.2,
          }}
        >
          <span style={{ fontSize: 7, textTransform: 'uppercase', letterSpacing: 0.5 }}>WK</span>
          <span style={{ fontSize: 18 }}>{week.week}</span>
        </div>

        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 15, fontWeight: 700 }}>{week.theme ?? `Week ${week.week}`}</span>
            {isCurrent && (
              <span
                style={{
                  background: 'linear-gradient(135deg,#7c3aed,#a855f7)',
                  color: '#fff',
                  borderRadius: 20,
                  padding: '2px 10px',
                  fontSize: 11,
                  fontWeight: 600,
                }}
              >
                Current
              </span>
            )}
          </div>
          {week.goals && week.goals.length > 0 && !isExpanded && (
            <div style={{ color: 'var(--text-2)', fontSize: 12, marginTop: 3 }}>
              {week.goals[0]}{week.goals.length > 1 ? ` +${week.goals.length - 1} more` : ''}
            </div>
          )}
        </div>

        {/* Indicators row */}
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexShrink: 0 }}>
          {week.mock_interview && (
            <span title="Mock Interview" style={{ fontSize: 16 }}>🎤</span>
          )}
          {week.checkpoint && (
            <span title="Checkpoint" style={{ fontSize: 16 }}>✅</span>
          )}
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--text-2)"
            strokeWidth="2.5"
            style={{ transform: isExpanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div
          style={{
            padding: '0 20px 20px',
            borderTop: '1px solid var(--border)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
            gap: 14,
          }}
        >
          {/* Goals */}
          {week.goals && week.goals.length > 0 && (
            <Section title="🎯 Goals" accent="#7c3aed">
              <ul style={{ margin: '6px 0 0 16px', padding: 0, listStyle: 'disc' }}>
                {week.goals.map((g, i) => (
                  <li key={i} style={{ color: 'var(--text)', fontSize: 13, marginBottom: 3 }}>{g}</li>
                ))}
              </ul>
            </Section>
          )}

          {/* Checklist */}
          {week.checklist && week.checklist.length > 0 && (
            <Section title="📝 Action Items" accent="#f43f5e">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6 }}>
                {week.checklist.map((item, i) => (
                  <label key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, cursor: 'pointer' }}>
                    <input 
                      type="checkbox" 
                      checked={item.is_completed} 
                      onChange={(e) => onToggleTask?.(i, e.target.checked)}
                      style={{ marginTop: 2, accentColor: '#f43f5e', flexShrink: 0 }} 
                    />
                    <span style={{ color: item.is_completed ? 'var(--text-2)' : 'var(--text)', textDecoration: item.is_completed ? 'line-through' : 'none', fontSize: 13, lineHeight: 1.4 }}>{item.task}</span>
                  </label>
                ))}
              </div>
            </Section>
          )}

          {/* DSA */}
          {week.dsa && (
            <Section title="💻 DSA" accent="#0ea5e9">
              {week.dsa.topics && week.dsa.topics.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 6 }}>
                  {week.dsa.topics.map((t) => (
                    <span key={t} style={{ background: 'rgba(14,165,233,0.1)', border: '1px solid rgba(14,165,233,0.2)', color: '#38bdf8', borderRadius: 20, padding: '2px 8px', fontSize: 11 }}>
                      {t}
                    </span>
                  ))}
                </div>
              )}
              {week.dsa.problems_target != null && (
                <div style={{ color: 'var(--text-2)', fontSize: 12, marginTop: 6 }}>
                  Target: <strong style={{ color: 'var(--text)' }}>{week.dsa.problems_target} problems</strong>
                </div>
              )}
              {week.dsa.resources && week.dsa.resources.length > 0 && (
                <div style={{ marginTop: 8, borderTop: '1px solid var(--border)', paddingTop: 6 }}>
                  <div style={{ fontSize: 10, color: 'var(--text-2)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>Resources</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {week.dsa.resources.map((res, i) => (
                      <a key={i} href={res.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: '#38bdf8', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 6, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        🔗 <span>{res.title}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </Section>
          )}

          {/* Core Subjects */}
          {week.core_subjects && week.core_subjects.length > 0 && (
            <Section title="📖 Core Subjects" accent="#10b981">
              {week.core_subjects.map((cs, i) => (
                <div key={i} style={{ marginTop: 6 }}>
                  <div style={{ color: 'var(--text)', fontSize: 13, fontWeight: 600 }}>{cs.subject}</div>
                  {cs.topics && cs.topics.length > 0 && (
                    <div style={{ color: 'var(--text-2)', fontSize: 12, marginTop: 2 }}>
                      {cs.topics.join(', ')}
                    </div>
                  )}
                  {cs.resource_url && (
                    <div style={{ marginTop: 4 }}>
                      <a href={cs.resource_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: '#34d399', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}>
                        🔗 {cs.resource_title || 'View Resource'}
                      </a>
                    </div>
                  )}
                </div>
              ))}
            </Section>
          )}

          {/* Aptitude */}
          {week.aptitude && (
            <Section title="🔢 Aptitude" accent="#f59e0b">
              <div style={{ color: 'var(--text)', fontSize: 13, marginTop: 6 }}>{week.aptitude}</div>
            </Section>
          )}

          {/* Projects */}
          {week.projects && (
            <Section title="🛠️ Projects" accent="#8b5cf6">
              <div style={{ color: 'var(--text)', fontSize: 13, marginTop: 6 }}>{week.projects}</div>
            </Section>
          )}

          {/* Mock Interview */}
          {week.mock_interview && (
            <Section title="🎤 Mock Interview" accent="#ec4899">
              <div style={{ color: 'var(--text-2)', fontSize: 13, marginTop: 6 }}>
                Mock interview scheduled for this week.
              </div>
            </Section>
          )}

          {/* Checkpoint */}
          {week.checkpoint && (
            <Section title="✅ Checkpoint" accent="#14b8a6">
              <div style={{ color: 'var(--text)', fontSize: 13, marginTop: 6 }}>{week.checkpoint}</div>
            </Section>
          )}
        </div>
      )}
    </div>
  );
}

function Section({ title, accent, children }: { title: string; accent: string; children: React.ReactNode }) {
  return (
    <div
      style={{
        background: 'var(--bg3)',
        border: '1px solid var(--border2)',
        borderRadius: 10,
        padding: '10px 14px',
        borderLeft: `3px solid ${accent}`,
      }}
    >
      <div style={{ color: accent, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5 }}>{title}</div>
      {children}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function RoadmapPage() {
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  useEffect(() => {
    StudentAPI.getRoadmap()
      .then((r) => {
        setRoadmap(r);
        // Auto-expand current week
        if (r.current_week) setExpanded(new Set([r.current_week]));
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  function toggleWeek(n: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(n)) next.delete(n);
      else next.add(n);
      return next;
    });
  }

  async function handleToggleTask(weekNum: number, taskIdx: number, isCompleted: boolean) {
    if (!roadmap) return;
    
    // Optimistic UI update
    setRoadmap((prev) => {
      if (!prev) return prev;
      const nextWeeks = prev.weeks_plan?.map((w) => {
        if (w.week !== weekNum) return w;
        const nextChecklist = [...(w.checklist || [])];
        if (nextChecklist[taskIdx]) {
          nextChecklist[taskIdx] = { ...nextChecklist[taskIdx], is_completed: isCompleted };
        }
        return { ...w, checklist: nextChecklist };
      });
      return { ...prev, weeks_plan: nextWeeks };
    });

    try {
      const res = await StudentAPI.updateChecklist(weekNum, taskIdx, isCompleted) as any;
      // Sync progress and week from server
      setRoadmap((prev) => {
        if (!prev) return prev;
        return { ...prev, completion_pct: res.completion_pct, current_week: res.current_week };
      });
    } catch (e) {
      console.error(e);
    }
  }

  async function handleDelete() {
    if (!confirm("Are you sure you want to redesign your roadmap? This will delete the current one.")) return;
    try {
      await StudentAPI.deleteRoadmap();
      setRoadmap(null);
    } catch (e) {
      alert("Failed to delete roadmap");
    }
  }

  if (loading) {
    return (
      <div style={{ maxWidth: 800, margin: '0 auto', padding: '40px 24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {[0, 1, 2, 3].map((i) => (
            <div key={i} style={{ height: 70, borderRadius: 14, background: 'var(--bg2)', border: '1px solid var(--border)', animation: 'pulse 1.5s ease-in-out infinite' }} />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: 800, margin: '0 auto', padding: '40px 24px', textAlign: 'center' }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>⚠️</div>
        <div style={{ color: 'var(--text)', fontWeight: 600, marginBottom: 8 }}>Failed to load roadmap</div>
        <div style={{ color: 'var(--text-2)', fontSize: 14 }}>{error}</div>
      </div>
    );
  }

  // Empty state
  if (!roadmap || !roadmap.current_week) {
    return (
      <div style={{ maxWidth: 800, margin: '0 auto', padding: '40px 24px', textAlign: 'center' }}>
        <div
          style={{
            background: 'var(--bg2)',
            border: '1px solid var(--border)',
            borderRadius: 20,
            padding: '60px 40px',
            maxWidth: 500,
            margin: '0 auto',
          }}
        >
          <div style={{ fontSize: 64, marginBottom: 16 }}>🗺️</div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: 'var(--text)', margin: '0 0 12px' }}>
            No Roadmap Yet
          </h2>
          <p style={{ color: 'var(--text-2)', fontSize: 15, margin: '0 0 28px', lineHeight: 1.6 }}>
            Let the AI Mentor generate a personalized placement roadmap based on your profile and target companies.
          </p>
          <Link
            href="/dashboard/chat"
            style={{
              display: 'inline-block',
              background: 'linear-gradient(135deg,#7c3aed,#a855f7)',
              color: '#fff',
              borderRadius: 12,
              padding: '12px 28px',
              fontSize: 15,
              fontWeight: 600,
              textDecoration: 'none',
              transition: 'opacity 0.2s',
            }}
          >
            🤖 Generate with AI Mentor →
          </Link>
        </div>
      </div>
    );
  }

  const pct = roadmap.completion_pct ?? 0;
  const weeks: RoadmapWeek[] = roadmap.weeks_plan ?? [];

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '32px 24px', color: 'var(--text)' }}>
      <style>{`@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }`}</style>

      {/* Header */}
      <div
        style={{
          background: 'var(--bg2)',
          border: '1px solid var(--border)',
          borderRadius: 16,
          padding: '24px 28px',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          gap: 24,
          flexWrap: 'wrap',
        }}
      >
        {/* Ring */}
        <div style={{ position: 'relative', flexShrink: 0 }}>
          <ProgressRing pct={Math.round(pct)} size={100} />
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <span style={{ fontSize: 20, fontWeight: 800 }}>{Math.round(pct)}%</span>
            <span style={{ fontSize: 10, color: 'var(--text-2)' }}>done</span>
          </div>
        </div>

        {/* Info */}
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: 20, fontWeight: 800, margin: '0 0 8px' }}>
            {roadmap.title ?? 'My Placement Roadmap'}
          </h1>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {roadmap.target_company && (
              <span style={{ background: 'rgba(124,58,237,0.15)', border: '1px solid rgba(124,58,237,0.3)', color: '#c4b5fd', borderRadius: 20, padding: '4px 12px', fontSize: 12, fontWeight: 600 }}>
                🏢 {roadmap.target_company}
              </span>
            )}
            {roadmap.target_role && (
              <span style={{ background: 'rgba(14,165,233,0.12)', border: '1px solid rgba(14,165,233,0.25)', color: '#7dd3fc', borderRadius: 20, padding: '4px 12px', fontSize: 12, fontWeight: 600 }}>
                💼 {roadmap.target_role}
              </span>
            )}
            {roadmap.current_week && roadmap.duration_weeks && (
              <span style={{ background: 'rgba(16,185,129,0.12)', border: '1px solid rgba(16,185,129,0.25)', color: '#6ee7b7', borderRadius: 20, padding: '4px 12px', fontSize: 12, fontWeight: 600 }}>
                📅 Week {roadmap.current_week} of {roadmap.duration_weeks}
              </span>
            )}
          </div>
        </div>

        {/* Expand all */}
        <div style={{ display: 'flex', gap: 10, flexShrink: 0 }}>
          <button
            onClick={() => {
              if (expanded.size === weeks.length) setExpanded(new Set());
              else setExpanded(new Set(weeks.map((w) => w.week)));
            }}
            style={{
              background: 'var(--bg3)',
              border: '1px solid var(--border2)',
              borderRadius: 10,
              padding: '8px 14px',
              color: 'var(--text-2)',
              fontSize: 12,
              cursor: 'pointer',
            }}
          >
            {expanded.size === weeks.length ? 'Collapse All' : 'Expand All'}
          </button>
          
          <button
            onClick={handleDelete}
            style={{
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.2)',
              borderRadius: 10,
              padding: '8px 14px',
              color: '#ef4444',
              fontSize: 12,
              cursor: 'pointer',
            }}
          >
            🗑️ Redesign Roadmap
          </button>
        </div>
      </div>

      {/* Week Cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {weeks.length === 0 ? (
          <div style={{ color: 'var(--text-2)', textAlign: 'center', padding: '32px 0', fontSize: 14 }}>
            No week data available in this roadmap.
          </div>
        ) : (
          weeks.map((w) => (
            <WeekCard
              key={w.week}
              week={w}
              isCurrent={w.week === roadmap.current_week}
              isExpanded={expanded.has(w.week)}
              onToggle={() => toggleWeek(w.week)}
              onToggleTask={(taskIdx, isCompleted) => handleToggleTask(w.week, taskIdx, isCompleted)}
            />
          ))
        )}
      </div>
    </div>
  );
}
