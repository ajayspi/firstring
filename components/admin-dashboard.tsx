'use client';

import React, { useState, useEffect, useMemo } from 'react';
import {
  Activity, Phone, Building2, TrendingUp, Search, RefreshCw,
  CheckCircle, XCircle, Clock, DollarSign, Users, AlertTriangle,
  BarChart3, List, Settings, LogOut, Bell,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const ADMIN_TOKEN = process.env.NEXT_PUBLIC_ADMIN_TOKEN || 'admin-token-12345';

type Tab = 'overview' | 'calls' | 'clinics' | 'analytics';

interface Call {
  id: string;
  owner_phone: string;
  caller_phone: string;
  started_at: string;
  duration_sec: number;
  state: string;
  outcome: string;
}

interface Clinic {
  phone: string;
  plan: string;
  calls: number;
  bookings: number;
  booking_rate: number;
  last_call: string | null;
  status: string;
}

const api = async (path: string) => {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${ADMIN_TOKEN}` },
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
};

const StatCard = ({
  label, value, sub, icon: Icon, accent = 'cyan',
}: {
  label: string; value: string | number; sub?: string;
  icon: any; accent?: string;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 12 }}
    animate={{ opacity: 1, y: 0 }}
    className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition"
  >
    <div className="flex items-start justify-between mb-3">
      <span className="text-xs uppercase tracking-wider text-slate-500 font-semibold">{label}</span>
      <Icon className={`w-4 h-4 text-${accent}-400`} />
    </div>
    <div className="text-3xl font-bold text-white tabular-nums">{value}</div>
    {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
  </motion.div>
);

const OutcomeBadge = ({ outcome }: { outcome: string }) => {
  const styles: Record<string, string> = {
    booking: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    voicemail: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    message: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
    dropped: 'bg-red-500/15 text-red-400 border-red-500/30',
  };
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-md text-xs font-medium border ${styles[outcome] || styles.message}`}>
      {outcome}
    </span>
  );
};

const fmtDuration = (sec: number) => `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`;
const fmtPhone = (p: string) => p?.replace('+91', '+91 ') || '—';
const fmtTime = (iso: string) =>
  iso ? new Date(iso).toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: 'short' }) : '—';

const Sparkline = ({ data, color = '#06b6d4' }: { data: number[]; color?: string }) => {
  const max = Math.max(...data, 1);
  const pts = data.map((v, i) => `${(i / (data.length - 1)) * 100},${40 - (v / max) * 34}`).join(' ');
  return (
    <svg viewBox="0 0 100 40" className="w-full h-16" preserveAspectRatio="none">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
      <polyline points={`0,40 ${pts} 100,40`} fill={color} opacity="0.08" stroke="none" />
    </svg>
  );
};

export default function AdminDashboard() {
  const [tab, setTab] = useState<Tab>('overview');
  const [health, setHealth] = useState<any>(null);
  const [calls, setCalls] = useState<Call[]>([]);
  const [clinics, setClinics] = useState<Clinic[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastSync, setLastSync] = useState<Date>(new Date());

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [h, c, cl, a] = await Promise.all([
        api('/admin/health'),
        api('/admin/calls?limit=100'),
        api('/admin/clinics'),
        api('/admin/analytics?days=7'),
      ]);
      setHealth(h);
      setCalls(c.items || []);
      setClinics(cl.items || []);
      setAnalytics(a);
      setLastSync(new Date());
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const t = setInterval(load, 30000); // poll every 30s
    return () => clearInterval(t);
  }, []);

  const filteredCalls = useMemo(
    () =>
      calls.filter(
        (c) =>
          !query ||
          c.id.toLowerCase().includes(query.toLowerCase()) ||
          c.owner_phone.includes(query) ||
          c.caller_phone.includes(query)
      ),
    [calls, query]
  );

  const dailyCalls = useMemo(
    () => (analytics?.by_day || []).map(([_, v]: any) => v.calls),
    [analytics]
  );

  const navItems: { key: Tab; label: string; icon: any }[] = [
    { key: 'overview', label: 'Overview', icon: Activity },
    { key: 'calls', label: 'Calls', icon: Phone },
    { key: 'clinics', label: 'Clinics', icon: Building2 },
    { key: 'analytics', label: 'Analytics', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white flex">
      {/* Sidebar */}
      <aside className="w-60 border-r border-slate-800 bg-slate-900/50 flex flex-col shrink-0">
        <div className="p-5 border-b border-slate-800">
          <div className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
            firstring
          </div>
          <div className="text-xs text-slate-500 mt-0.5">Admin Console</div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                tab === key
                  ? 'bg-cyan-500/15 text-cyan-400'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </nav>
        <div className="p-3 border-t border-slate-800 space-y-1">
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition">
            <Settings className="w-4 h-4" /> Settings
          </button>
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-slate-800 transition">
            <LogOut className="w-4 h-4" /> Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Topbar */}
        <header className="h-16 border-b border-slate-800 px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold capitalize">{tab}</h1>
            <span className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-full border ${
              error
                ? 'bg-red-500/10 text-red-400 border-red-500/30'
                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${error ? 'bg-red-400' : 'bg-emerald-400 animate-pulse'}`} />
              {error ? 'API offline' : 'Live'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500">
              Synced {lastSync.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
            <button
              onClick={load}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition relative">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-cyan-400 rounded-full" />
            </button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-xs font-bold">
              A
            </div>
          </div>
        </header>

        {/* Error banner */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="bg-red-500/10 border-b border-red-500/30 px-6 py-3 flex items-center gap-3 text-sm text-red-300"
            >
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>Cannot reach API at <code className="font-mono text-xs">{API_BASE}</code> — {error}</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content */}
        <main className="flex-1 overflow-auto p-6">
          {/* OVERVIEW */}
          {tab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard label="Calls Today" value={health?.system?.calls_today ?? '—'} icon={Phone} sub={`${health?.system?.total_calls ?? 0} total`} />
                <StatCard label="Active Clinics" value={health?.system?.total_clinics ?? '—'} icon={Building2} accent="blue" sub="registered" />
                <StatCard label="Bookings" value={analytics?.summary?.total_bookings ?? '—'} icon={CheckCircle} accent="emerald" sub="last 7 days" />
                <StatCard
                  label="Booking Rate"
                  value={analytics?.summary ? `${(analytics.summary.booking_rate * 100).toFixed(0)}%` : '—'}
                  icon={TrendingUp}
                  accent="violet"
                  sub="conversion"
                />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="font-semibold">Call Volume</h2>
                    <span className="text-xs text-slate-500">Last 7 days</span>
                  </div>
                  {dailyCalls.length > 0 ? (
                    <Sparkline data={dailyCalls} />
                  ) : (
                    <div className="h-16 flex items-center justify-center text-sm text-slate-600">No data yet</div>
                  )}
                  <div className="flex justify-between text-xs text-slate-600 mt-2">
                    {(analytics?.by_day || []).map(([day]: any) => (
                      <span key={day}>{new Date(day).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}</span>
                    ))}
                  </div>
                </div>

                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                  <h2 className="font-semibold mb-4">System</h2>
                  <div className="space-y-3 text-sm">
                    {[
                      ['API', 'operational'],
                      ['ASR vendor', 'pending'],
                      ['LLM vendor', 'pending'],
                      ['Database', 'in-memory'],
                    ].map(([k, v]) => (
                      <div key={k} className="flex items-center justify-between">
                        <span className="text-slate-400">{k}</span>
                        <span className={`flex items-center gap-1.5 text-xs ${
                          v === 'operational' ? 'text-emerald-400'
                          : v === 'pending' ? 'text-amber-400'
                          : 'text-slate-400'
                        }`}>
                          {v === 'operational' ? <CheckCircle className="w-3 h-3" />
                            : v === 'pending' ? <Clock className="w-3 h-3" />
                            : <XCircle className="w-3 h-3" />}
                          {v}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                  <h2 className="font-semibold">Recent Calls</h2>
                  <button onClick={() => setTab('calls')} className="text-xs text-cyan-400 hover:text-cyan-300">
                    View all →
                  </button>
                </div>
                <CallTable calls={calls.slice(0, 5)} />
              </div>
            </div>
          )}

          {/* CALLS */}
          {tab === 'calls' && (
            <div className="space-y-4">
              <div className="relative max-w-md">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search by call ID, clinic, or caller number"
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-sm placeholder:text-slate-600 focus:outline-none focus:border-cyan-500 transition"
                />
              </div>
              <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
                <CallTable calls={filteredCalls} />
              </div>
            </div>
          )}

          {/* CLINICS */}
          {tab === 'clinics' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-slate-900/80 border-b border-slate-800">
                  <tr className="text-left text-xs uppercase tracking-wider text-slate-500">
                    <th className="px-6 py-3 font-semibold">Clinic</th>
                    <th className="px-6 py-3 font-semibold">Plan</th>
                    <th className="px-6 py-3 font-semibold text-right">Calls</th>
                    <th className="px-6 py-3 font-semibold text-right">Bookings</th>
                    <th className="px-6 py-3 font-semibold text-right">Rate</th>
                    <th className="px-6 py-3 font-semibold">Last Call</th>
                    <th className="px-6 py-3 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {clinics.length === 0 ? (
                    <tr><td colSpan={7} className="px-6 py-12 text-center text-slate-600">No clinics registered</td></tr>
                  ) : (
                    clinics.map((c) => (
                      <tr key={c.phone} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition">
                        <td className="px-6 py-4 font-mono text-xs">{fmtPhone(c.phone)}</td>
                        <td className="px-6 py-4">
                          <span className="text-xs px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 capitalize">
                            {c.plan}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right tabular-nums">{c.calls}</td>
                        <td className="px-6 py-4 text-right tabular-nums text-emerald-400">{c.bookings}</td>
                        <td className="px-6 py-4 text-right tabular-nums">
                          <span className={c.booking_rate >= 0.5 ? 'text-emerald-400' : c.booking_rate > 0 ? 'text-amber-400' : 'text-slate-500'}>
                            {(c.booking_rate * 100).toFixed(0)}%
                          </span>
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-500">{fmtTime(c.last_call)}</td>
                        <td className="px-6 py-4">
                          <span className="flex items-center gap-1.5 text-xs text-emerald-400">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> {c.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* ANALYTICS */}
          {tab === 'analytics' && analytics && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatCard label="Total Calls" value={analytics.summary.total_calls} icon={Phone} />
                <StatCard label="Bookings" value={analytics.summary.total_bookings} icon={CheckCircle} accent="emerald" />
                <StatCard label="Booking Rate" value={`${(analytics.summary.booking_rate * 100).toFixed(0)}%`} icon={TrendingUp} accent="violet" />
                <StatCard label="Avg Duration" value={`${Math.floor(analytics.summary.avg_call_duration_sec / 60)}m ${Math.round(analytics.summary.avg_call_duration_sec % 60)}s`} icon={Clock} accent="blue" />
              </div>

              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                <h2 className="font-semibold mb-6">Daily Breakdown ({analytics.period_days} days)</h2>
                <div className="space-y-3">
                  {analytics.by_day.map(([day, v]: any) => (
                    <div key={day} className="flex items-center gap-4">
                      <span className="text-xs text-slate-500 w-20">{new Date(day).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}</span>
                      <div className="flex-1 flex gap-1 h-6">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${(v.calls / Math.max(...analytics.by_day.map((x: any) => x[1].calls), 1)) * 100}%` }}
                          className="bg-cyan-500/40 rounded-l"
                        />
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${(v.bookings / Math.max(...analytics.by_day.map((x: any) => x[1].calls), 1)) * 100}%` }}
                          className="bg-emerald-500/70 rounded-r"
                        />
                      </div>
                      <span className="text-xs tabular-nums text-slate-400 w-24 text-right">
                        {v.calls} calls · {v.bookings} booked
                      </span>
                    </div>
                  ))}
                </div>
                <div className="flex gap-4 mt-4 text-xs text-slate-500">
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded bg-cyan-500/40" /> Calls</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded bg-emerald-500/70" /> Bookings</span>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function CallTable({ calls }: { calls: Call[] }) {
  if (!calls.length) {
    return <div className="px-6 py-12 text-center text-slate-600 text-sm">No calls yet</div>;
  }
  return (
    <table className="w-full text-sm">
      <thead className="bg-slate-900/80 border-b border-slate-800">
        <tr className="text-left text-xs uppercase tracking-wider text-slate-500">
          <th className="px-6 py-3 font-semibold">Call ID</th>
          <th className="px-6 py-3 font-semibold">Clinic</th>
          <th className="px-6 py-3 font-semibold">Caller</th>
          <th className="px-6 py-3 font-semibold">Time</th>
          <th className="px-6 py-3 font-semibold text-right">Duration</th>
          <th className="px-6 py-3 font-semibold">Outcome</th>
        </tr>
      </thead>
      <tbody>
        {calls.map((c) => (
          <tr key={c.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition">
            <td className="px-6 py-3 font-mono text-xs text-slate-400">{c.id}</td>
            <td className="px-6 py-3 font-mono text-xs">{fmtPhone(c.owner_phone)}</td>
            <td className="px-6 py-3 font-mono text-xs text-slate-400">{fmtPhone(c.caller_phone)}</td>
            <td className="px-6 py-3 text-xs text-slate-500">{fmtTime(c.started_at)}</td>
            <td className="px-6 py-3 text-right tabular-nums text-slate-300">{fmtDuration(c.duration_sec)}</td>
            <td className="px-6 py-3"><OutcomeBadge outcome={c.outcome} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
