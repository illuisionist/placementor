'use client';
import { useState, useEffect } from 'react';
import { StudentAPI, StudentProfile } from '@/lib/api';

export default function ProfilePage() {
  const [profile, setProfile] = useState<StudentProfile>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    StudentAPI.getProfile()
      .then(d => setProfile(d.profile || {}))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const toList = (val: string): string[] => val ? val.split(',').map(s => s.trim()).filter(Boolean) : [];
  const fromList = (arr?: string[]): string => (arr || []).join(', ');

  const save = async () => {
    setSaving(true);
    setMsg(null);
    try {
      await StudentAPI.updateProfile(profile);
      setMsg({ type: 'success', text: '✅ Profile saved successfully!' });
    } catch (e) {
      setMsg({ type: 'error', text: `❌ ${(e as Error).message}` });
    } finally {
      setSaving(false);
      setTimeout(() => setMsg(null), 3000);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-slate-400 animate-pulse text-sm">Loading profile...</div>
    </div>
  );

  const inputClass = "w-full px-4 py-2.5 rounded-lg text-sm outline-none transition-all focus:ring-2 focus:ring-purple-500/40";
  const inputStyle = { background: 'var(--bg2)', border: '1px solid var(--border2)', color: 'var(--text)' };
  const labelClass = "block text-xs font-semibold text-slate-400 mb-1.5";

  return (
    <div className="fade-in">
      <div className="mb-7">
        <h1 className="text-3xl font-black tracking-tight">👤 My Profile</h1>
        <p className="text-slate-400 text-sm mt-1">Keep your profile updated for accurate recommendations</p>
      </div>

      <div className="p-8 rounded-2xl border" style={{ background: 'var(--bg3)', borderColor: 'var(--border)' }}>
        <div className="grid grid-cols-2 gap-5 mb-5">
          <div>
            <label className={labelClass}>Branch</label>
            <input className={inputClass} style={inputStyle} placeholder="e.g. CSE, ECE, ME"
              value={profile.branch || ''} onChange={e => setProfile(p => ({ ...p, branch: e.target.value }))} />
          </div>
          <div>
            <label className={labelClass}>Semester</label>
            <input type="number" min={1} max={8} className={inputClass} style={inputStyle} placeholder="e.g. 7"
              value={profile.semester || ''} onChange={e => setProfile(p => ({ ...p, semester: +e.target.value }))} />
          </div>
          <div>
            <label className={labelClass}>CGPA</label>
            <input type="number" step={0.1} min={0} max={10} className={inputClass} style={inputStyle} placeholder="e.g. 8.5"
              value={profile.cgpa || ''} onChange={e => setProfile(p => ({ ...p, cgpa: +e.target.value }))} />
          </div>
          <div>
            <label className={labelClass}>Graduation Year</label>
            <input type="number" className={inputClass} style={inputStyle} placeholder="e.g. 2025"
              value={profile.graduation_year || ''} onChange={e => setProfile(p => ({ ...p, graduation_year: +e.target.value }))} />
          </div>
          <div className="col-span-2">
            <label className={labelClass}>Skills (comma separated)</label>
            <input className={inputClass} style={inputStyle} placeholder="Python, DSA, React, SQL, Machine Learning"
              value={fromList(profile.skills)} onChange={e => setProfile(p => ({ ...p, skills: toList(e.target.value) }))} />
          </div>
          <div className="col-span-2">
            <label className={labelClass}>Target Companies (comma separated)</label>
            <input className={inputClass} style={inputStyle} placeholder="Amazon, Microsoft, Google, Infosys"
              value={fromList(profile.preferred_companies)} onChange={e => setProfile(p => ({ ...p, preferred_companies: toList(e.target.value) }))} />
          </div>
          <div className="col-span-2">
            <label className={labelClass}>Preferred Domains (comma separated)</label>
            <input className={inputClass} style={inputStyle} placeholder="SDE, Data Science, DevOps"
              value={fromList(profile.preferred_domains)} onChange={e => setProfile(p => ({ ...p, preferred_domains: toList(e.target.value) }))} />
          </div>
          <div>
            <label className={labelClass}>LeetCode Handle</label>
            <input className={inputClass} style={inputStyle} placeholder="your_leetcode_handle"
              value={profile.leetcode_handle || ''} onChange={e => setProfile(p => ({ ...p, leetcode_handle: e.target.value }))} />
          </div>
          <div>
            <label className={labelClass}>GitHub Handle</label>
            <input className={inputClass} style={inputStyle} placeholder="your_github_handle"
              value={profile.github_handle || ''} onChange={e => setProfile(p => ({ ...p, github_handle: e.target.value }))} />
          </div>
          <div className="col-span-2">
            <label className={labelClass}>LinkedIn URL</label>
            <input className={inputClass} style={inputStyle} placeholder="https://linkedin.com/in/yourname"
              value={profile.linkedin_url || ''} onChange={e => setProfile(p => ({ ...p, linkedin_url: e.target.value }))} />
          </div>
        </div>

        {msg && (
          <div className={`p-3 rounded-lg text-sm mb-4 border ${msg.type === 'success' ? 'text-green-300' : 'text-red-300'}`}
            style={{ background: msg.type === 'success' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', borderColor: msg.type === 'success' ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)' }}>
            {msg.text}
          </div>
        )}

        <button onClick={save} disabled={saving}
          className="px-6 py-2.5 rounded-lg text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50"
          style={{ background: 'linear-gradient(135deg,#7c3aed,#a855f7)' }}>
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
      </div>
    </div>
  );
}
