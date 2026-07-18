'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { ResumeAPI, Resume } from '@/lib/api';

// ─── Circular ATS Ring ────────────────────────────────────────────────────────

function ATSRing({ score, size = 140 }: { score: number; size?: number }) {
  const [animated, setAnimated] = useState(0);
  const r = (size - 14) / 2;
  const circ = 2 * Math.PI * r;

  useEffect(() => {
    const t = setTimeout(() => setAnimated(score), 100);
    return () => clearTimeout(t);
  }, [score]);

  const dash = circ * (animated / 100);
  const color = score >= 70 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444';
  const label = score >= 70 ? 'Strong' : score >= 50 ? 'Average' : 'Needs Work';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
      <div style={{ position: 'relative' }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--border2)" strokeWidth={10} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={10}
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circ}`}
            style={{ transition: 'stroke-dasharray 1.2s cubic-bezier(0.4,0,0.2,1)' }}
          />
        </svg>
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
          <span style={{ fontSize: 28, fontWeight: 800, color }}>{animated}</span>
          <span style={{ fontSize: 11, color: 'var(--text-2)' }}>/ 100</span>
        </div>
      </div>
      <span style={{ fontSize: 13, fontWeight: 600, color }}>{label}</span>
    </div>
  );
}

// ─── Priority Badge ───────────────────────────────────────────────────────────

function PriorityBadge({ priority }: { priority: string }) {
  const map: Record<string, { bg: string; border: string; color: string }> = {
    HIGH: { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)', color: '#fca5a5' },
    MEDIUM: { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.3)', color: '#fcd34d' },
    LOW: { bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.3)', color: '#6ee7b7' },
  };
  const style = map[priority.toUpperCase()] ?? map.LOW;
  return (
    <span
      style={{
        background: style.bg,
        border: `1px solid ${style.border}`,
        color: style.color,
        borderRadius: 20,
        padding: '2px 8px',
        fontSize: 10,
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: 0.5,
        flexShrink: 0,
      }}
    >
      {priority}
    </span>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function ResumePage() {
  const [dragging, setDragging] = useState(false);
  const [dragName, setDragName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<{ filename: string; next_step: string } | null>(null);
  const [uploadError, setUploadError] = useState('');
  const [activeResume, setActiveResume] = useState<Resume | null>(null);
  const [resumeLoading, setResumeLoading] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load existing active resume
  useEffect(() => {
    ResumeAPI.list()
      .then((list) => {
        const active = list.find((r) => r.is_active) ?? list[0] ?? null;
        setActiveResume(active);
      })
      .catch(() => setActiveResume(null))
      .finally(() => setResumeLoading(false));
  }, []);

  const handleFile = useCallback(async (file: File) => {
    const allowed = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    const extOk = file.name.endsWith('.pdf') || file.name.endsWith('.docx');
    if (!allowed.includes(file.type) && !extOk) {
      setUploadError('Only .pdf and .docx files are supported.');
      return;
    }
    setUploadError('');
    setUploadResult(null);
    setUploading(true);
    try {
      const res = await ResumeAPI.upload(file);
      setUploadResult({ filename: file.name, next_step: res.next_step });
      // Refresh resume list
      const list = await ResumeAPI.list();
      const active = list.find((r) => r.is_active) ?? list[0] ?? null;
      setActiveResume(active);
      // Poll for ATS results (background analysis takes a few seconds)
      let pollCount = 0;
      const pollInterval = setInterval(async () => {
        pollCount++;
        if (pollCount > 10) { clearInterval(pollInterval); return; }
        try {
          const resumes = await ResumeAPI.list();
          const polledActive = resumes.find((r: Resume) => r.is_active);
          if (polledActive?.ats_score) {
            setActiveResume(polledActive);
            clearInterval(pollInterval);
          }
        } catch {}
      }, 3000);
    } catch (e) {
      setUploadError((e as Error).message ?? 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  }, []);

  // Drag events
  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); setDragging(true); setDragName(e.dataTransfer.items[0]?.kind === 'file' ? 'Drop to upload' : ''); };
  const onDragLeave = () => { setDragging(false); setDragName(''); };
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    setDragName('');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };
  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = '';
  };

  const showAnalysis = !!activeResume?.ats_score;

  return (
    <div style={{ maxWidth: 820, margin: '0 auto', padding: '32px 24px', color: 'var(--text)' }}>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 800, margin: '0 0 6px' }}>📄 Resume Analyzer</h1>
        <p style={{ color: 'var(--text-2)', fontSize: 14, margin: 0 }}>
          Upload your resume to get ATS score, strengths, weaknesses & actionable suggestions.
        </p>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          background: dragging ? 'rgba(124,58,237,0.1)' : 'var(--bg2)',
          border: `2px dashed ${dragging ? '#7c3aed' : 'var(--border2)'}`,
          borderRadius: 16,
          padding: '48px 32px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'background 0.2s, border-color 0.2s',
          marginBottom: 20,
          position: 'relative',
        }}
      >
        {uploading ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 44,
                height: 44,
                border: '3px solid var(--border2)',
                borderTopColor: '#7c3aed',
                borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
              }}
            />
            <div style={{ color: 'var(--text-2)', fontSize: 14 }}>Uploading & analyzing your resume…</div>
          </div>
        ) : dragging ? (
          <div>
            <div style={{ fontSize: 40, marginBottom: 8 }}>📂</div>
            <div style={{ color: '#a78bfa', fontSize: 15, fontWeight: 600 }}>
              {dragName || 'Drop your file here'}
            </div>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: 44, marginBottom: 12 }}>📤</div>
            <div style={{ color: 'var(--text)', fontSize: 16, fontWeight: 600, marginBottom: 6 }}>
              Drag & drop your resume here
            </div>
            <div style={{ color: 'var(--text-2)', fontSize: 13, marginBottom: 16 }}>
              Supports <strong>.pdf</strong> and <strong>.docx</strong> files
            </div>
            <div
              style={{
                display: 'inline-block',
                background: 'linear-gradient(135deg,#7c3aed,#a855f7)',
                color: '#fff',
                borderRadius: 10,
                padding: '10px 20px',
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              Browse File
            </div>
          </div>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx"
          onChange={onFileChange}
          style={{ display: 'none' }}
        />
      </div>

      {/* Upload Error */}
      {uploadError && (
        <div
          style={{
            background: 'rgba(239,68,68,0.08)',
            border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: 12,
            padding: '14px 18px',
            marginBottom: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            animation: 'fadeIn 0.3s ease',
          }}
        >
          <span style={{ fontSize: 20 }}>⚠️</span>
          <div style={{ flex: 1, color: '#fca5a5', fontSize: 14 }}>{uploadError}</div>
          <button
            onClick={() => { setUploadError(''); fileInputRef.current?.click(); }}
            style={{ background: 'rgba(239,68,68,0.15)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, padding: '6px 14px', color: '#fca5a5', fontSize: 12, cursor: 'pointer', fontWeight: 600 }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Upload Success */}
      {uploadResult && !uploadError && (
        <div
          style={{
            background: 'rgba(16,185,129,0.08)',
            border: '1px solid rgba(16,185,129,0.3)',
            borderRadius: 12,
            padding: '16px 20px',
            marginBottom: 20,
            animation: 'fadeIn 0.3s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 24 }}>✅</span>
            <div style={{ flex: 1 }}>
              <div style={{ color: '#6ee7b7', fontWeight: 700, fontSize: 14 }}>
                {uploadResult.filename} uploaded successfully!
              </div>
              {uploadResult.next_step && (
                <div style={{ color: 'var(--text-2)', fontSize: 13, marginTop: 4 }}>
                  {uploadResult.next_step}
                </div>
              )}
            </div>
            <Link
              href="/dashboard/chat"
              style={{
                background: 'linear-gradient(135deg,#7c3aed,#a855f7)',
                color: '#fff',
                borderRadius: 10,
                padding: '8px 16px',
                fontSize: 13,
                fontWeight: 600,
                textDecoration: 'none',
                flexShrink: 0,
              }}
            >
              Analyze in Chat →
            </Link>
          </div>
        </div>
      )}

      {/* ATS Analysis */}
      {!resumeLoading && showAnalysis && activeResume && (
        <div style={{ animation: 'fadeIn 0.4s ease' }}>
          {/* Score + Overview */}
          <div
            style={{
              background: 'var(--bg2)',
              border: '1px solid var(--border)',
              borderRadius: 16,
              padding: '28px 32px',
              marginBottom: 16,
              display: 'flex',
              alignItems: 'center',
              gap: 32,
              flexWrap: 'wrap',
            }}
          >
            <ATSRing score={activeResume.ats_score!} />
            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ fontSize: 11, color: 'var(--text-2)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 }}>
                ATS Analysis Report
              </div>
              <div style={{ fontSize: 18, fontWeight: 800, marginBottom: 4 }}>{activeResume.original_name}</div>
              <div style={{ color: 'var(--text-2)', fontSize: 13 }}>
                Version {activeResume.version} · Uploaded {new Date(activeResume.uploaded_at).toLocaleDateString()}
              </div>
              <div style={{ marginTop: 12 }}>
                <Link
                  href="/dashboard/chat"
                  style={{
                    display: 'inline-block',
                    background: 'linear-gradient(135deg,#7c3aed,#a855f7)',
                    color: '#fff',
                    borderRadius: 10,
                    padding: '8px 18px',
                    fontSize: 13,
                    fontWeight: 600,
                    textDecoration: 'none',
                  }}
                >
                  🤖 Discuss with AI →
                </Link>
              </div>
            </div>
          </div>

          {/* 3-column grid: Strengths / Weaknesses / Suggestions */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
              gap: 14,
            }}
          >
            {/* Strengths */}
            {activeResume.strengths && activeResume.strengths.length > 0 && (
              <div
                style={{
                  background: 'var(--bg2)',
                  border: '1px solid rgba(16,185,129,0.2)',
                  borderRadius: 14,
                  padding: '18px 20px',
                  borderLeft: '3px solid #10b981',
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 700, color: '#10b981', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  💪 Strengths
                </div>
                <ul style={{ margin: 0, padding: '0 0 0 16px', listStyle: 'disc' }}>
                  {activeResume.strengths.map((s, i) => (
                    <li key={i} style={{ color: 'var(--text)', fontSize: 13, marginBottom: 6, lineHeight: 1.5 }}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Weaknesses */}
            {activeResume.weaknesses && activeResume.weaknesses.length > 0 && (
              <div
                style={{
                  background: 'var(--bg2)',
                  border: '1px solid rgba(245,158,11,0.2)',
                  borderRadius: 14,
                  padding: '18px 20px',
                  borderLeft: '3px solid #f59e0b',
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 700, color: '#f59e0b', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  ⚠️ Weaknesses
                </div>
                <ul style={{ margin: 0, padding: '0 0 0 16px', listStyle: 'disc' }}>
                  {activeResume.weaknesses.map((w, i) => (
                    <li key={i} style={{ color: 'var(--text)', fontSize: 13, marginBottom: 6, lineHeight: 1.5 }}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Suggestions */}
            {activeResume.suggestions && activeResume.suggestions.length > 0 && (
              <div
                style={{
                  background: 'var(--bg2)',
                  border: '1px solid rgba(99,102,241,0.2)',
                  borderRadius: 14,
                  padding: '18px 20px',
                  borderLeft: '3px solid #6366f1',
                  gridColumn: activeResume.strengths?.length && activeResume.weaknesses?.length ? 'span 1' : 'auto',
                }}
              >
                <div style={{ fontSize: 13, fontWeight: 700, color: '#818cf8', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  💡 Suggestions
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {activeResume.suggestions.map((s, i) => (
                    <div
                      key={i}
                      style={{
                        background: 'var(--bg3)',
                        border: '1px solid var(--border2)',
                        borderRadius: 10,
                        padding: '10px 12px',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: s.fix ? 6 : 0 }}>
                        <PriorityBadge priority={s.priority} />
                        <span style={{ color: 'var(--text)', fontSize: 13, lineHeight: 1.5 }}>{s.suggestion}</span>
                      </div>
                      {s.fix && (
                        <div style={{ color: 'var(--text-2)', fontSize: 12, marginTop: 4, paddingLeft: 2 }}>
                          <strong style={{ color: '#a78bfa' }}>Fix:</strong> {s.fix}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Loading skeleton for existing resume */}
      {resumeLoading && (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 16, padding: 28, height: 200, animation: 'pulse 1.5s ease-in-out infinite' }} />
      )}

      {/* No resume, no analysis state */}
      {!resumeLoading && !showAnalysis && !uploadResult && !uploading && (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 14, padding: '28px 24px', textAlign: 'center' }}>
          <div style={{ fontSize: 36, marginBottom: 10 }}>📊</div>
          <div style={{ color: 'var(--text-2)', fontSize: 14 }}>
            Upload a resume above to see your ATS score and detailed feedback.
          </div>
        </div>
      )}

      <style>{`@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }`}</style>
    </div>
  );
}
