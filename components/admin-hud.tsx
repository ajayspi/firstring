'use client';

import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity, Phone, Building2, TrendingUp, Search, Command, Radio,
  CheckCircle2, XCircle, Clock, Zap, Wifi, WifiOff, ChevronRight,
  PhoneIncoming, PhoneMissed, CalendarCheck, Volume2, Pause, Play,
  ArrowUpRight, ArrowDownRight, Circle, Cpu, Database, Cloud,
  Mic, MicOff, Languages, MapPin, X, ExternalLink, Copy,
} from 'lucide-react';

/* ─────────────────────────────────────────────────────────────
   CONFIG
   ───────────────────────────────────────────────────────────── */
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000';
const ADMIN_TOKEN = process.env.NEXT_PUBLIC_ADMIN_TOKEN || 'admin-token-12345';

type Outcome = 'booking' | 'message' | 'voicemail' | 'dropped';

interface Call {
  id: string;
  owner_phone: string;
  caller_phone: string;
  started_at: number;
  duration_sec: number;
  outcome: Outcome;
  language: string;
  live?: boolean;
  turn?: string;
}

interface Clinic {
  phone: string;
  name: string;
  plan: string;
  calls: number;
  bookings: number;
  booking_rate: number;
  last_call: number | null;
  status: string;
}

/* ─────────────────────────────────────────────────────────────
   DATA — real API with simulated live fallback
   ───────────────────────────────────────────────────────────── */
const CLINICS: Clinic[] = [
  { phone: '+919876543210', name: 'Sunrise Dental', plan: 'pro', calls: 0, bookings: 0, booking_rate: 0, last_call: null, status: 'active' },
  { phone: '+919876543211', name: 'Glow Salon & Spa', plan: 'pro', calls: 0, bookings: 0, booking_rate: 0, last_call: null, status: 'active' },
  { phone: '+919876543212', name: 'Apollo Clinic', plan: 'free', calls: 0, bookings: 0, booking_rate: 0, last_call: null, status: 'active' },
  { phone: '+919876543213', name: 'Lotus Wellness', plan: 'free', calls: 0, bookings: 0, booking_rate: 0, last_call: null, status: 'paused' },
];

const LANGS = ['Hindi', 'English', 'Hinglish', 'Tamil', 'Marathi'];
const TURNS = ['greeting', 'listening', 'slot-check', 'confirming', 'booking'];
const OUTCOMES: Outcome[] = ['booking', 'booking', 'booking', 'message', 'voicemail', 'dropped'];

let callSeq = 0;
function makeCall(live = false): Call {
  callSeq += 1;
  const clinic = CLINICS[Math.floor(Math.random() * CLINICS.length)];
  const outcome = live ? 'message' : OUTCOMES[Math.floor(Math.random() * OUTCOMES.length)];
  return {
    id: `call_${(callSeq + 4820).toString(36).toUpperCase()}`,
    owner_phone: clinic.phone,
    caller_phone: `+919${Math.floor(100000000 + Math.random() * 899999999)}`,
    started_at: Date.now(),
    duration_sec: live ? 0 : Math.floor(Math.random() * 420) + 25,
    outcome,
    language: LANGS[Math.floor(Math.random() * LANGS.length)],
    live,
    turn: live ? TURNS[Math.floor(Math.random() * TURNS.length)] : undefined,
  };
}

function seedHistory(n = 68): Call[] {
  const now = Date.now();
  return Array.from({ length: n }, (_, i) => {
    const c = makeCall(false);
    return { ...c, started_at: now - i * (1000 * 60 * 7 + Math.random() * 1e6) };
  });
}

/* ─────────────────────────────────────────────────────────────
   PRIMITIVES
   ───────────────────────────────────────────────────────────── */
function useCounter(target: number, duration = 900) {
  const [val, setVal] = useState(0);
  const from = useRef(0);
  useEffect(() => {
    const start = performance.now();
    const a = from.current;
    let raf = 0;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / duration);
      const e = 1 - Math.pow(1 - p, 3);
      setVal(a + (target - a) * e);
      if (p < 1) raf = requestAnimationFrame(tick);
      else from.current = target;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, duration]);
  return val;
}

const fmtPhone = (p: string) => (p?.startsWith('+91') ? `+91 ${p.slice(3, 8)} ${p.slice(8)}` : p || '—');
/* the admin API carries no clinic name — map the demo numbers, else show the phone */
const nameOf = (phone: string) => CLINICS.find((c) => c.phone === phone)?.name || fmtPhone(phone);
const fmtDur = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
const fmtAgo = (t: number) => {
  const d = Math.floor((Date.now() - t) / 1000);
  if (d < 60) return `${d}s ago`;
  if (d < 3600) return `${Math.floor(d / 60)}m ago`;
  return `${Math.floor(d / 3600)}h ago`;
};

function Spark({ data, color = '#22d3ee', h = 28 }: { data: number[]; color?: string; h?: number }) {
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const rng = max - min || 1;
  const pts = data.map((v, i) => `${(i / Math.max(data.length - 1, 1)) * 100},${h - ((v - min) / rng) * (h - 4) - 2}`).join(' ');
  return (
    <svg viewBox={`0 0 100 ${h}`} className="w-full" style={{ height: h }} preserveAspectRatio="none">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
      <polyline points={`${pts} 100,${h} 0,${h}`} fill={color} opacity="0.10" stroke="none" />
    </svg>
  );
}

function Gauge({ value, max = 100, label, unit = '%', size = 118, color = '#22d3ee' }: {
  value: number; max?: number; label: string; unit?: string; size?: number; color?: string;
}) {
  const pct = Math.max(0, Math.min(1, value / max));
  const r = size / 2 - 10;
  const circ = Math.PI * r * 1.5; // 270° arc
  const animated = useCounter(pct * 100, 1100);
  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-[135deg]">
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke="rgba(148,163,184,0.13)" strokeWidth="7"
          strokeDasharray={`${circ} ${circ * 3}`} strokeLinecap="round"
        />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={color} strokeWidth="7"
          strokeDasharray={`${(animated / 100) * circ} ${circ * 3}`}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 6px ${color}88)` }}
        />
      </svg>
      <div className="-mt-[74px] text-center" style={{ marginTop: -(size * 0.63) }}>
        <div className="font-mono text-2xl font-bold tabular-nums text-white leading-none">
          {animated.toFixed(unit === '%' ? 0 : 1)}
          <span className="text-sm text-slate-500">{unit}</span>
        </div>
      </div>
      <div className="mt-8 text-[10px] uppercase tracking-[0.15em] text-slate-500 text-center leading-tight">{label}</div>
    </div>
  );
}

/* Canvas oscilloscope — live voice activity */
function Oscilloscope({ active, color = '#22d3ee' }: { active: boolean; color?: string }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const resize = () => {
      const w = canvas.clientWidth || 600;
      const h = canvas.clientHeight || 120;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    window.addEventListener('resize', resize);

    let raf = 0;
    let t = 0;
    let amp = active ? 1 : 0.12;
    const draw = () => {
      const w = canvas.clientWidth || 600;
      const h = canvas.clientHeight || 120;
      ctx.clearRect(0, 0, w, h);

      // grid
      ctx.strokeStyle = 'rgba(148,163,184,0.07)';
      ctx.lineWidth = 1;
      for (let x = 0; x < w; x += 32) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
      for (let y = 0; y < h; y += 24) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }

      // centre line
      ctx.strokeStyle = 'rgba(148,163,184,0.15)';
      ctx.beginPath(); ctx.moveTo(0, h / 2); ctx.lineTo(w, h / 2); ctx.stroke();

      // target amplitude
      const target = active ? 1 : 0.12;
      amp += (target - amp) * 0.04;
      t += active ? 0.055 : 0.012;

      // main waveform
      ctx.beginPath();
      for (let x = 0; x <= w; x++) {
        const n =
          Math.sin(x * 0.021 + t) * 0.55 +
          Math.sin(x * 0.007 - t * 0.7) * 0.3 +
          Math.sin(x * 0.061 + t * 1.9) * 0.15;
        const jitter = active ? (Math.random() - 0.5) * 3 : 0;
        const y = h / 2 + n * (h * 0.36) * amp + jitter;
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.8;
      ctx.shadowBlur = active ? 12 : 3;
      ctx.shadowColor = color;
      ctx.stroke();
      ctx.shadowBlur = 0;

      // mirrored ghost
      ctx.beginPath();
      for (let x = 0; x <= w; x++) {
        const n = Math.sin(x * 0.021 - t * 0.9) * 0.5 + Math.sin(x * 0.013 + t) * 0.3;
        const y = h / 2 + n * (h * 0.36) * amp * 0.6;
        x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.strokeStyle = 'rgba(34,211,238,0.25)';
      ctx.lineWidth = 1;
      ctx.stroke();

      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize); };
  }, [active, color]);
  return <canvas ref={ref} className="w-full h-full block" />;
}

/* Interactive area chart with hover crosshair */
function AreaChart({ series, height = 190 }: { series: { label: string; data: number[]; color: string }[]; height?: number }) {
  const [hover, setHover] = useState<number | null>(null);
  const [w, setW] = useState(760);
  const hostRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = hostRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setW(el.clientWidth || 760));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const n = series[0]?.data.length || 0;
  const max = Math.max(...series.flatMap((s) => s.data), 1);
  const padT = 14, padB = 22;
  const innerH = height - padT - padB;
  const xAt = (i: number) => (i / Math.max(n - 1, 1)) * w;
  const yAt = (v: number) => padT + innerH - (v / max) * innerH;

  const path = (data: number[]) => data.map((v, i) => `${i === 0 ? 'M' : 'L'}${xAt(i)},${yAt(v)}`).join(' ');
  const area = (data: number[]) => `${path(data)} L${xAt(n - 1)},${padT + innerH} L0,${padT + innerH} Z`;

  return (
    <div ref={hostRef} className="relative w-full select-none">
      <svg
        width={w} height={height} className="w-full"
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          const i = Math.round(((e.clientX - rect.left) / rect.width) * (n - 1));
          setHover(Math.max(0, Math.min(n - 1, i)));
        }}
        onMouseLeave={() => setHover(null)}
      >
        <defs>
          {series.map((s, si) => (
            <linearGradient key={si} id={`g${si}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={s.color} stopOpacity="0.30" />
              <stop offset="100%" stopColor={s.color} stopOpacity="0" />
            </linearGradient>
          ))}
        </defs>

        {/* grid */}
        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <g key={f}>
            <line x1={0} x2={w} y1={padT + innerH * f} y2={padT + innerH * f} stroke="rgba(148,163,184,0.09)" strokeWidth="1" />
            <text x={4} y={padT + innerH * f - 4} fill="rgba(100,116,139,0.8)" fontSize="9" fontFamily="monospace">
              {Math.round(max * (1 - f))}
            </text>
          </g>
        ))}

        {series.map((s, si) => (
          <g key={si}>
            <path d={area(s.data)} fill={`url(#g${si})`} />
            <motion.path
              d={path(s.data)} fill="none" stroke={s.color} strokeWidth="2"
              strokeLinejoin="round" strokeLinecap="round"
              initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.1, ease: 'easeOut' }}
              style={{ filter: `drop-shadow(0 0 5px ${s.color}66)` }}
            />
          </g>
        ))}

        {hover !== null && (
          <g>
            <line x1={xAt(hover)} x2={xAt(hover)} y1={padT} y2={padT + innerH} stroke="rgba(226,232,240,0.35)" strokeWidth="1" strokeDasharray="3 3" />
            {series.map((s, si) => (
              <circle key={si} cx={xAt(hover)} cy={yAt(s.data[hover])} r="4" fill="#0b1220" stroke={s.color} strokeWidth="2" />
            ))}
          </g>
        )}
      </svg>

      <AnimatePresence>
        {hover !== null && (
          <motion.div
            initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="pointer-events-none absolute top-1 z-10 rounded-lg border border-slate-700 bg-slate-900/95 px-3 py-2 shadow-xl backdrop-blur"
            style={{ left: Math.min(Math.max(xAt(hover) - 46, 0), w - 116) }}
          >
            <div className="mb-1 text-[10px] uppercase tracking-wider text-slate-500">
              {new Date(Date.now() - (n - 1 - hover) * 86400000).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
            </div>
            {series.map((s) => (
              <div key={s.label} className="flex items-center gap-2 text-xs">
                <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
                <span className="text-slate-400">{s.label}</span>
                <span className="ml-auto font-mono font-semibold text-white tabular-nums">{s.data[hover]}</span>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      <div className="mt-1 flex justify-between px-1 text-[10px] text-slate-600">
        {[0, Math.floor(n / 2), n - 1].map((i) => (
          <span key={i}>{new Date(Date.now() - (n - 1 - i) * 86400000).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}</span>
        ))}
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   OUTCOME STYLES
   ───────────────────────────────────────────────────────────── */
const OUTCOME_META: Record<Outcome, { color: string; bg: string; icon: any; label: string }> = {
  booking: { color: 'text-emerald-400', bg: 'bg-emerald-500/12 border-emerald-500/30', icon: CalendarCheck, label: 'Booked' },
  message: { color: 'text-sky-400', bg: 'bg-sky-500/12 border-sky-500/30', icon: Volume2, label: 'Message' },
  voicemail: { color: 'text-amber-400', bg: 'bg-amber-500/12 border-amber-500/30', icon: PhoneMissed, label: 'Voicemail' },
  dropped: { color: 'text-rose-400', bg: 'bg-rose-500/12 border-rose-500/30', icon: XCircle, label: 'Dropped' },
};

const OutcomeChip = ({ outcome }: { outcome: Outcome }) => {
  const m = OUTCOME_META[outcome];
  const Icon = m.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-[11px] font-medium ${m.bg} ${m.color}`}>
      <Icon className="h-3 w-3" /> {m.label}
    </span>
  );
};

/* ─────────────────────────────────────────────────────────────
   MAIN
   ───────────────────────────────────────────────────────────── */
export default function AdminHUD() {
  const [booted, setBooted] = useState(false);
  const [online, setOnline] = useState(false);
  const [live, setLive] = useState(true);
  const [calls, setCalls] = useState<Call[]>(() => seedHistory());
  const [activeCall, setActiveCall] = useState<Call>(() => makeCall(true));
  const [detail, setDetail] = useState<Call | null>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [filter, setFilter] = useState<'all' | Outcome>('all');
  const [query, setQuery] = useState('');
  const [clock, setClock] = useState(new Date());
  const [pulse, setPulse] = useState(0);
  const [realClinics, setRealClinics] = useState<any[] | null>(null);

  /* boot sequence */
  useEffect(() => {
    const t = setTimeout(() => setBooted(true), 620);
    return () => clearTimeout(t);
  }, []);

  /* clock */
  useEffect(() => {
    const t = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  /* probe real API */
  useEffect(() => {
    let alive = true;
    const probe = async () => {
      try {
        const r = await fetch(`${API_BASE}/admin/health`, {
          headers: { Authorization: `Bearer ${ADMIN_TOKEN}` },
          signal: AbortSignal.timeout(2500),
        });
        if (alive && r.ok) setOnline(true);
      } catch {
        if (alive) setOnline(false);
      }
    };
    probe();
    const t = setInterval(probe, 15000);
    return () => { alive = false; clearInterval(t); };
  }, []);

  /* real data when the API is up — simulation is the fallback, not the default */
  useEffect(() => {
    if (!online) return;
    let alive = true;
    const load = async () => {
      try {
        const h = { Authorization: `Bearer ${ADMIN_TOKEN}` };
        const [cr, gr] = await Promise.all([
          fetch(`${API_BASE}/admin/calls?limit=200`, { headers: h, signal: AbortSignal.timeout(5000) }),
          fetch(`${API_BASE}/admin/clinics`, { headers: h, signal: AbortSignal.timeout(5000) }),
        ]);
        if (!alive || !cr.ok || !gr.ok) return;
        const cj = await cr.json();
        const gj = await gr.json();
        if (!alive) return;
        const mapped: Call[] = (cj.items || []).map((r: any, i: number) => ({
          id: r.id,
          owner_phone: r.owner_phone,
          caller_phone: r.caller_phone,
          started_at: Date.parse(r.started_at) || Date.now() - i * 60000,
          duration_sec: r.duration_sec ?? 0,
          // ponytail: unknown outcomes collapse to 'message'; tighten if the
          // backend ever emits a value outside OUTCOME_META
          outcome: (OUTCOME_META[r.outcome as Outcome] ? r.outcome : 'message') as Outcome,
          language: r.language || '—',
        }));
        if (mapped.length) setCalls(mapped);
        setRealClinics(gj.items || []);
      } catch {
        /* keep whatever we already have on screen */
      }
    };
    load();
    const t = setInterval(load, 30000);
    return () => { alive = false; clearInterval(t); };
  }, [online]);

  /* live call simulation — only when no API is linked */
  useEffect(() => {
    if (!live || online) return;
    const t = setInterval(() => {
      setPulse((p) => p + 1);
      setCalls((prev) => {
        // finalise the previous live call into history
        const finalised = { ...activeCall, live: false, duration_sec: 40 + Math.floor(Math.random() * 300), started_at: Date.now() - 1000 };
        return [finalised, ...prev].slice(0, 400);
      });
      setActiveCall(makeCall(true));
    }, 6500);
    return () => clearInterval(t);
  }, [live, online, activeCall]);

  /* command palette hotkey */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
      if (e.key === 'Escape') { setPaletteOpen(false); setDetail(null); }
      if (e.key === ' ' && e.target === document.body) { e.preventDefault(); setLive((v) => !v); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  /* derived metrics */
  const stats = useMemo(() => {
    const total = calls.length;
    const bookings = calls.filter((c) => c.outcome === 'booking').length;
    const answered = calls.filter((c) => c.outcome !== 'dropped').length;
    const avgDur = calls.reduce((a, c) => a + c.duration_sec, 0) / Math.max(total, 1);
    const today = calls.filter((c) => Date.now() - c.started_at < 86400000).length;
    const yest = calls.filter((c) => {
      const d = Date.now() - c.started_at;
      return d >= 86400000 && d < 172800000;
    }).length;
    return {
      total, bookings, today, yest,
      bookingRate: (bookings / Math.max(total, 1)) * 100,
      answerRate: (answered / Math.max(total, 1)) * 100,
      avgDur,
      delta: yest ? Math.round(((today - yest) / yest) * 100) : 0,
    };
  }, [calls]);

  const series = useMemo(() => {
    const days = 14;
    const buckets = Array.from({ length: days }, () => ({ c: 0, b: 0 }));
    calls.forEach((c) => {
      const idx = days - 1 - Math.floor((Date.now() - c.started_at) / 86400000);
      if (idx >= 0 && idx < days) {
        buckets[idx].c += 1;
        if (c.outcome === 'booking') buckets[idx].b += 1;
      }
    });
    return [
      { label: 'Calls', data: buckets.map((b) => b.c), color: '#22d3ee' },
      { label: 'Bookings', data: buckets.map((b) => b.b), color: '#34d399' },
    ];
  }, [calls, pulse]);

  const clinicRows = useMemo(() => {
    if (realClinics) {
      return realClinics.map((r: any) => ({
        ...r,
        name: nameOf(r.phone),
        booking_rate: r.booking_rate ?? r.bookings / Math.max(r.calls, 1),
      }));
    }
    const map = new Map<string, Clinic>();
    CLINICS.forEach((c) => map.set(c.phone, { ...c }));
    calls.forEach((c) => {
      const row = map.get(c.owner_phone);
      if (!row) return;
      row.calls += 1;
      if (c.outcome === 'booking') row.bookings += 1;
      if (!row.last_call || c.started_at > row.last_call) row.last_call = c.started_at;
    });
    return [...map.values()]
      .map((r) => ({ ...r, booking_rate: r.bookings / Math.max(r.calls, 1) }))
      .sort((a, b) => b.calls - a.calls);
  }, [calls, pulse, realClinics]);

  const visibleCalls = useMemo(() => {
    const q = query.trim().toLowerCase();
    return calls
      .filter((c) => filter === 'all' || c.outcome === filter)
      .filter((c) => !q || c.id.toLowerCase().includes(q) || c.caller_phone.includes(q) || c.owner_phone.includes(q))
      .slice(0, 120);
  }, [calls, filter, query]);

  const streamCalls = useMemo(() => calls.slice(0, 7), [calls, pulse]);

  /* ── render ───────────────────────────────────────────────── */
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#05080f] text-slate-200 antialiased">
      {/* ── ambient background ── */}
      <div className="pointer-events-none fixed inset-0">
        <div
          className="absolute inset-0 opacity-[0.30]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(34,211,238,0.055) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,0.055) 1px, transparent 1px)',
            backgroundSize: '44px 44px',
            maskImage: 'radial-gradient(ellipse 90% 65% at 50% 0%, #000 40%, transparent 100%)',
          }}
        />
        <motion.div
          animate={{ y: ['-10%', '110%'] }}
          transition={{ duration: 7, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-cyan-400/40 to-transparent"
        />
        <div className="absolute -left-40 -top-40 h-[520px] w-[520px] rounded-full bg-cyan-500/10 blur-[130px]" />
        <div className="absolute -bottom-52 -right-32 h-[520px] w-[520px] rounded-full bg-emerald-500/10 blur-[130px]" />
      </div>

      {/* ── boot overlay ── */}
      <AnimatePresence>
        {!booted && (
          <motion.div
            exit={{ opacity: 0 }} transition={{ duration: 0.4 }}
            className="fixed inset-0 z-[100] flex items-center justify-center bg-[#05080f]"
          >
            <div className="w-72 text-center">
              <motion.div
                initial={{ scale: 0.85, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                className="mb-5 font-mono text-2xl font-bold tracking-[0.28em] text-cyan-400"
              >
                FIRSTRING
              </motion.div>
              <div className="h-0.5 w-full overflow-hidden rounded bg-slate-800">
                <motion.div
                  initial={{ x: '-100%' }} animate={{ x: '0%' }} transition={{ duration: 0.6, ease: 'easeInOut' }}
                  className="h-full w-full bg-gradient-to-r from-cyan-400 to-emerald-400"
                />
              </div>
              <div className="mt-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-600">
                initialising console
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={booted ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="relative z-10 mx-auto max-w-[1600px] px-5 pb-16 pt-5"
      >
        {/* ══ TOP BAR ══ */}
        <header className="mb-6 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-cyan-500/40 bg-cyan-500/10">
              <Radio className="h-5 w-5 text-cyan-400" />
              {live && (
                <motion.span
                  animate={{ scale: [1, 1.9], opacity: [0.6, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="absolute inset-0 rounded-xl border border-cyan-400"
                />
              )}
            </div>
            <div>
              <div className="font-mono text-lg font-bold tracking-[0.18em] text-white">FIRSTRING</div>
              <div className="text-[10px] uppercase tracking-[0.22em] text-slate-500">Operations Console</div>
            </div>
          </div>

          <div className="ml-auto flex flex-wrap items-center gap-2.5">
            {/* connection */}
            <div className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium ${
              online ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                     : 'border-amber-500/30 bg-amber-500/10 text-amber-400'
            }`}>
              <span className={`h-1.5 w-1.5 rounded-full ${online ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`} />
              {online ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
              <span className="hidden sm:inline">{online ? 'API linked' : 'Simulation'}</span>
            </div>

            {/* live toggle */}
            <button
              onClick={() => setLive((v) => !v)}
              className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-medium transition ${
                live ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20'
                     : 'border-slate-700 bg-slate-800/60 text-slate-400 hover:text-white'
              }`}
            >
              {live ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
              {live ? 'Live' : 'Paused'}
            </button>

            {/* command hint */}
            <button
              onClick={() => setPaletteOpen(true)}
              className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2 text-xs text-slate-400 transition hover:border-slate-600 hover:text-white"
            >
              <Search className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Search</span>
              <kbd className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-500">⌘K</kbd>
            </button>

            <div className="rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2 font-mono text-xs tabular-nums text-slate-300">
              {clock.toLocaleTimeString('en-IN', { hour12: false })}
              <span className="ml-2 text-slate-600">IST</span>
            </div>
          </div>
        </header>

        {/* ══ ACTIVE CALL STRIP ══ */}
        <motion.section
          layout
          className="relative mb-5 overflow-hidden rounded-2xl border border-cyan-500/20 bg-gradient-to-r from-cyan-500/[0.07] via-slate-900/50 to-emerald-500/[0.05] backdrop-blur"
        >
          <div className="grid gap-4 p-4 md:grid-cols-[1.1fr_1.4fr_auto] md:items-center">
            {/* who */}
            <div className="flex items-center gap-4">
              <div className="relative flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border border-cyan-500/40 bg-cyan-500/10">
                <PhoneIncoming className="h-5 w-5 text-cyan-400" />
                <motion.span
                  animate={{ scale: [1, 1.7], opacity: [0.5, 0] }}
                  transition={{ duration: 1.8, repeat: Infinity }}
                  className="absolute inset-0 rounded-xl border border-cyan-400"
                />
              </div>
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeCall.id}
                  initial={{ opacity: 0, x: 12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -12 }}
                  transition={{ duration: 0.35 }}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-cyan-400">On call</span>
                    <span className="font-mono text-[10px] text-slate-500">{activeCall.id}</span>
                  </div>
                  <div className="font-mono text-lg font-semibold text-white">{fmtPhone(activeCall.caller_phone)}</div>
                  <div className="flex items-center gap-3 text-[11px] text-slate-400">
                    <span className="flex items-center gap-1"><MapPin className="h-3 w-3" />{nameOf(activeCall.owner_phone)}</span>
                    <span className="flex items-center gap-1"><Languages className="h-3 w-3" />{activeCall.language}</span>
                  </div>
                </motion.div>
              </AnimatePresence>
            </div>

            {/* waveform */}
            <div className="h-[92px] w-full overflow-hidden rounded-xl border border-slate-800/80 bg-slate-950/50">
              <Oscilloscope active={live} />
            </div>

            {/* turn indicator */}
            <div className="flex items-center gap-3 md:flex-col md:items-end">
              <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/70 px-3 py-2">
                <Mic className="h-3.5 w-3.5 text-emerald-400" />
                <span className="font-mono text-xs text-slate-300">{activeCall.turn}</span>
              </div>
              <div className="flex items-center gap-1.5">
                {TURNS.map((t) => (
                  <span
                    key={t}
                    className={`h-1.5 w-1.5 rounded-full transition ${
                      TURNS.indexOf(t) <= TURNS.indexOf(activeCall.turn || 'greeting')
                        ? 'bg-cyan-400' : 'bg-slate-700'
                    }`}
                  />
                ))}
              </div>
            </div>
          </div>
          {/* progress line */}
          <motion.div
            animate={{ x: ['-100%', '100%'] }}
            transition={{ duration: 2.4, repeat: Infinity, ease: 'linear' }}
            className="h-px w-1/3 bg-gradient-to-r from-transparent via-cyan-400/70 to-transparent"
          />
        </motion.section>

        {/* ══ KPI STRIP ══ */}
        <section className="mb-5 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[
            { label: 'Calls today', value: stats.today, icon: Phone, color: '#22d3ee', delta: stats.delta, spark: series[0].data.slice(-8) },
            { label: 'Bookings', value: stats.bookings, icon: CalendarCheck, color: '#34d399', delta: 18, spark: series[1].data.slice(-8) },
            { label: 'Booking rate', value: stats.bookingRate, unit: '%', icon: TrendingUp, color: '#a78bfa', delta: 6, spark: series[1].data.map((b, i) => (b / Math.max(series[0].data[i], 1)) * 100).slice(-8) },
            { label: 'Avg duration', value: stats.avgDur, unit: 's', icon: Clock, color: '#fbbf24', delta: -4, spark: series[0].data.slice(-8).map((v) => v * 9 + 40) },
          ].map((kpi, i) => (
            <KpiCard key={kpi.label} {...kpi} delay={i * 0.06} />
          ))}
        </section>

        {/* ══ MAIN GRID ══ */}
        <section className="grid grid-cols-1 gap-5 xl:grid-cols-[300px_1fr_270px]">
          {/* ── live stream ── */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur">
            <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-cyan-400" />
                <h2 className="text-sm font-semibold text-white">Live Stream</h2>
              </div>
              {live && (
                <span className="flex items-center gap-1.5 font-mono text-[10px] text-emerald-400">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" /> REC
                </span>
              )}
            </div>
            <div className="max-h-[430px] space-y-1.5 overflow-y-auto p-3">
              <AnimatePresence initial={false}>
                {streamCalls.map((c, i) => (
                  <motion.button
                    key={c.id}
                    layout
                    initial={{ opacity: 0, y: -14, scale: 0.97 }}
                    animate={{ opacity: i === 0 ? 1 : 0.95 - i * 0.09, y: 0, scale: 1 }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.35, ease: 'easeOut' }}
                    onClick={() => setDetail(c)}
                    className="group w-full rounded-xl border border-slate-800/80 bg-slate-900/60 p-3 text-left transition hover:border-cyan-500/40 hover:bg-slate-800/60"
                  >
                    <div className="mb-1.5 flex items-center justify-between gap-2">
                      <span className="font-mono text-xs font-semibold text-slate-200">{fmtPhone(c.caller_phone)}</span>
                      <span className="font-mono text-[10px] text-slate-600">{fmtAgo(c.started_at)}</span>
                    </div>
                    <div className="mb-2 flex items-center gap-2 text-[10px] text-slate-500">
                      <Building2 className="h-3 w-3" />
                      {nameOf(c.owner_phone)}
                      <span className="ml-auto flex items-center gap-1"><Languages className="h-2.5 w-2.5" />{c.language}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <OutcomeChip outcome={c.outcome} />
                      <span className="font-mono text-[10px] tabular-nums text-slate-500">{fmtDur(c.duration_sec)}</span>
                    </div>
                  </motion.button>
                ))}
              </AnimatePresence>
            </div>
          </div>

          {/* ── centre column ── */}
          <div className="space-y-5">
            {/* chart */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-sm font-semibold text-white">Call &amp; Booking Volume</h2>
                  <p className="text-[11px] text-slate-500">Rolling 14 days · hover for detail</p>
                </div>
                <div className="flex items-center gap-4 text-[11px]">
                  {series.map((s) => (
                    <span key={s.label} className="flex items-center gap-1.5 text-slate-400">
                      <span className="h-2 w-2 rounded-full" style={{ background: s.color, boxShadow: `0 0 8px ${s.color}` }} />
                      {s.label}
                      <span className="font-mono font-semibold text-slate-200">
                        {s.data.reduce((a, b) => a + b, 0)}
                      </span>
                    </span>
                  ))}
                </div>
              </div>
              <AreaChart series={series} />
            </div>

            {/* call ledger */}
            <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/40 backdrop-blur">
              <div className="flex flex-wrap items-center gap-3 border-b border-slate-800 px-5 py-3">
                <h2 className="text-sm font-semibold text-white">Call Ledger</h2>
                <div className="flex items-center gap-1 rounded-lg border border-slate-800 bg-slate-950/60 p-0.5">
                  {(['all', 'booking', 'message', 'voicemail', 'dropped'] as const).map((f) => (
                    <button
                      key={f}
                      onClick={() => setFilter(f)}
                      className={`rounded-md px-2.5 py-1 text-[11px] font-medium capitalize transition ${
                        filter === f ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-500 hover:text-slate-300'
                      }`}
                    >
                      {f}
                    </button>
                  ))}
                </div>
                <span className="ml-auto font-mono text-[11px] text-slate-600">{visibleCalls.length} rows</span>
              </div>
              <div className="max-h-[360px] overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur">
                    <tr className="text-[10px] uppercase tracking-wider text-slate-500">
                      <th className="px-5 py-2.5 font-semibold">Call</th>
                      <th className="px-3 py-2.5 font-semibold">Clinic</th>
                      <th className="px-3 py-2.5 font-semibold">Caller</th>
                      <th className="px-3 py-2.5 font-semibold">Lang</th>
                      <th className="px-3 py-2.5 text-right font-semibold">Dur</th>
                      <th className="px-3 py-2.5 font-semibold">Outcome</th>
                      <th className="px-5 py-2.5" />
                    </tr>
                  </thead>
                  <tbody>
                    {visibleCalls.map((c) => (
                      <tr
                        key={c.id}
                        onClick={() => setDetail(c)}
                        className="cursor-pointer border-t border-slate-800/50 transition hover:bg-cyan-500/[0.05]"
                      >
                        <td className="px-5 py-2.5 font-mono text-[11px] text-slate-400">{c.id}</td>
                        <td className="px-3 py-2.5 text-slate-300">{nameOf(c.owner_phone)}</td>
                        <td className="px-3 py-2.5 font-mono text-[11px] text-slate-400">{fmtPhone(c.caller_phone)}</td>
                        <td className="px-3 py-2.5 text-slate-500">{c.language}</td>
                        <td className="px-3 py-2.5 text-right font-mono tabular-nums text-slate-300">{fmtDur(c.duration_sec)}</td>
                        <td className="px-3 py-2.5"><OutcomeChip outcome={c.outcome} /></td>
                        <td className="px-5 py-2.5 text-right">
                          <ChevronRight className="ml-auto h-3.5 w-3.5 text-slate-600" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* ── right rail ── */}
          <div className="space-y-5">
            {/* gauges */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur">
              <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
                <Zap className="h-4 w-4 text-cyan-400" /> Performance
              </h2>
              <div className="grid grid-cols-2 gap-2">
                <Gauge value={stats.bookingRate} label="Booking rate" color="#34d399" />
                <Gauge value={stats.answerRate} label="Answer rate" color="#22d3ee" />
              </div>
            </div>

            {/* system health */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur">
              <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
                <Cpu className="h-4 w-4 text-cyan-400" /> Subsystems
              </h2>
              <div className="space-y-3">
                {[
                  { name: 'Telephony', icon: Phone, status: online ? 'operational' : 'degraded' },
                  { name: 'ASR vendor', icon: Mic, status: 'pending' },
                  { name: 'LLM vendor', icon: Cpu, status: 'pending' },
                  { name: 'TTS vendor', icon: Volume2, status: 'pending' },
                  { name: 'Postgres', icon: Database, status: 'degraded' },
                  { name: 'WhatsApp', icon: Cloud, status: 'pending' },
                ].map((s) => {
                  const Icon = s.icon;
                  const meta =
                    s.status === 'operational' ? { c: 'text-emerald-400', d: 'bg-emerald-400', t: 'up' }
                    : s.status === 'degraded' ? { c: 'text-amber-400', d: 'bg-amber-400', t: 'warn' }
                    : { c: 'text-slate-500', d: 'bg-slate-600', t: 'n/a' };
                  return (
                    <div key={s.name} className="flex items-center gap-2.5">
                      <Icon className="h-3.5 w-3.5 text-slate-500" />
                      <span className="text-xs text-slate-400">{s.name}</span>
                      <span className={`ml-auto flex items-center gap-1.5 font-mono text-[10px] ${meta.c}`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${meta.d} ${s.status === 'operational' ? 'animate-pulse' : ''}`} />
                        {meta.t}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* clinics mini */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur">
              <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-white">
                <Building2 className="h-4 w-4 text-cyan-400" /> Clinics
              </h2>
              <div className="space-y-3">
                {clinicRows.map((c) => (
                  <div key={c.phone} className="group">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="truncate text-xs font-medium text-slate-200">{c.name}</span>
                      <span className={`ml-auto rounded px-1.5 py-0.5 text-[9px] uppercase tracking-wide ${
                        c.plan === 'pro' ? 'bg-violet-500/15 text-violet-300' : 'bg-slate-800 text-slate-500'
                      }`}>{c.plan}</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-slate-800">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(100, (c.bookings / Math.max(c.calls, 1)) * 100)}%` }}
                        transition={{ duration: 0.9, ease: 'easeOut' }}
                        className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400"
                      />
                    </div>
                    <div className="mt-1 flex justify-between font-mono text-[10px] text-slate-500">
                      <span>{c.calls} calls</span>
                      <span className="text-emerald-400">{c.bookings} booked</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* ══ FOOTER ══ */}
        <footer className="mt-6 flex flex-wrap items-center gap-3 font-mono text-[10px] uppercase tracking-[0.18em] text-slate-600">
          <span>firstring console</span>
          <span className="text-slate-800">/</span>
          <span>build {callSeq.toString(36).toUpperCase()}</span>
          <span className="text-slate-800">/</span>
          <span className={online ? 'text-emerald-500' : 'text-amber-500'}>{online ? 'api linked' : 'simulation mode'}</span>
          <span className="ml-auto">press space to {live ? 'pause' : 'resume'} · ⌘K to search</span>
        </footer>
      </motion.div>

      {/* ══ COMMAND PALETTE ══ */}
      <CommandPalette
        open={paletteOpen}
        onClose={() => setPaletteOpen(false)}
        clinics={clinicRows}
        calls={calls}
        onSelectCall={(c) => { setDetail(c); setPaletteOpen(false); }}
        onPickClinic={(name) => { setQuery(''); setFilter('all'); setPaletteOpen(false); }}
      />

      {/* ══ DETAIL DRAWER ══ */}
      <CallDrawer call={detail} onClose={() => setDetail(null)} />
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────
   KPI CARD
   ───────────────────────────────────────────────────────────── */
function KpiCard({ label, value, unit, icon: Icon, color, delta, spark, delay }: {
  label: string; value: number; unit?: string; icon: any; color: string;
  delta?: number; spark: number[]; delay: number;
}) {
  const animated = useCounter(value, 1000);
  const up = (delta ?? 0) >= 0;
  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay, duration: 0.45 }}
      whileHover={{ y: -3 }}
      className="group relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/40 p-5 backdrop-blur transition hover:border-slate-700"
    >
      <div className="absolute inset-x-0 top-0 h-px" style={{ background: `linear-gradient(90deg, transparent, ${color}88, transparent)` }} />
      <div className="mb-3 flex items-start justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</span>
        <span className="flex h-7 w-7 items-center justify-center rounded-lg" style={{ background: `${color}1a` }}>
          <Icon className="h-3.5 w-3.5" style={{ color }} />
        </span>
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="font-mono text-3xl font-bold tabular-nums text-white">
          {animated.toFixed(unit === '%' ? 0 : 0)}
        </span>
        {unit && <span className="font-mono text-sm text-slate-500">{unit}</span>}
        {delta !== undefined && (
          <span className={`ml-auto flex items-center gap-0.5 font-mono text-[11px] ${up ? 'text-emerald-400' : 'text-rose-400'}`}>
            {up ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
            {Math.abs(delta)}%
          </span>
        )}
      </div>
      <div className="mt-3 -mb-1">
        <Spark data={spark} color={color} h={26} />
      </div>
    </motion.div>
  );
}

/* ─────────────────────────────────────────────────────────────
   COMMAND PALETTE
   ───────────────────────────────────────────────────────────── */
function CommandPalette({ open, onClose, clinics, calls, onSelectCall, onPickClinic }: {
  open: boolean; onClose: () => void; clinics: Clinic[]; calls: Call[];
  onSelectCall: (c: Call) => void; onPickClinic: (name: string) => void;
}) {
  const [q, setQ] = useState('');
  const [sel, setSel] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) { setQ(''); setSel(0); setTimeout(() => inputRef.current?.focus(), 40); }
  }, [open]);

  const results = useMemo(() => {
    const term = q.trim().toLowerCase();
    const items: { kind: string; label: string; hint: string; run: () => void }[] = [];

    if (!term) {
      clinics.slice(0, 3).forEach((c) =>
        items.push({ kind: 'clinic', label: c.name, hint: `${c.calls} calls · ${c.bookings} booked`, run: () => onPickClinic(c.name) })
      );
      calls.slice(0, 5).forEach((c) =>
        items.push({ kind: 'call', label: fmtPhone(c.caller_phone), hint: `${c.id} · ${c.outcome}`, run: () => onSelectCall(c) })
      );
    } else {
      clinics.filter((c) => c.name.toLowerCase().includes(term)).slice(0, 5).forEach((c) =>
        items.push({ kind: 'clinic', label: c.name, hint: `${c.calls} calls`, run: () => onPickClinic(c.name) })
      );
      calls
        .filter((c) => c.id.toLowerCase().includes(term) || c.caller_phone.includes(term) || c.owner_phone.includes(term))
        .slice(0, 8)
        .forEach((c) => items.push({ kind: 'call', label: fmtPhone(c.caller_phone), hint: `${c.id} · ${c.outcome}`, run: () => onSelectCall(c) }));
    }
    return items;
  }, [q, clinics, calls, onSelectCall, onPickClinic]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowDown') { e.preventDefault(); setSel((s) => Math.min(s + 1, results.length - 1)); }
      if (e.key === 'ArrowUp') { e.preventDefault(); setSel((s) => Math.max(s - 1, 0)); }
      if (e.key === 'Enter' && results[sel]) { e.preventDefault(); results[sel].run(); onClose(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, results, sel, onClose]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 z-[90] flex items-start justify-center bg-black/70 px-4 pt-[12vh] backdrop-blur-sm"
        >
          <motion.div
            initial={{ opacity: 0, y: -16, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.98 }}
            transition={{ duration: 0.18 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-xl overflow-hidden rounded-2xl border border-cyan-500/25 bg-slate-900/95 shadow-2xl shadow-cyan-500/10 backdrop-blur-xl"
          >
            <div className="flex items-center gap-3 border-b border-slate-800 px-4 py-3">
              <Command className="h-4 w-4 text-cyan-400" />
              <input
                ref={inputRef}
                value={q}
                onChange={(e) => { setQ(e.target.value); setSel(0); }}
                placeholder="Search calls, clinics, numbers…"
                className="flex-1 bg-transparent text-sm text-white placeholder:text-slate-600 focus:outline-none"
              />
              <kbd className="rounded border border-slate-700 bg-slate-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-500">esc</kbd>
            </div>
            <div className="max-h-80 overflow-y-auto p-2">
              {results.length === 0 ? (
                <div className="px-3 py-8 text-center text-sm text-slate-600">No matches</div>
              ) : (
                results.map((r, i) => (
                  <button
                    key={i}
                    onMouseEnter={() => setSel(i)}
                    onClick={() => { r.run(); onClose(); }}
                    className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition ${
                      sel === i ? 'bg-cyan-500/15' : 'hover:bg-slate-800/60'
                    }`}
                  >
                    <span className={`flex h-7 w-7 items-center justify-center rounded-lg ${
                      r.kind === 'clinic' ? 'bg-violet-500/15 text-violet-300' : 'bg-cyan-500/15 text-cyan-300'
                    }`}>
                      {r.kind === 'clinic' ? <Building2 className="h-3.5 w-3.5" /> : <Phone className="h-3.5 w-3.5" />}
                    </span>
                    <span className="flex-1 truncate">
                      <span className="block text-sm text-slate-200">{r.label}</span>
                      <span className="block font-mono text-[10px] text-slate-500">{r.hint}</span>
                    </span>
                    {sel === i && <ChevronRight className="h-3.5 w-3.5 text-cyan-400" />}
                  </button>
                ))
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/* ─────────────────────────────────────────────────────────────
   CALL DRAWER
   ───────────────────────────────────────────────────────────── */
function CallDrawer({ call, onClose }: { call: Call | null; onClose: () => void }) {
  const [copied, setCopied] = useState(false);
  const script = useMemo(() => {
    if (!call) return [];
    if (call.outcome === 'booking') {
      return [
        { role: 'ai', text: `Namaste! ${nameOf(call.owner_phone)}, main aapki kaise madad kar sakti hoon?` },
        { role: 'caller', text: 'Mujhe kal ke liye appointment chahiye.' },
        { role: 'ai', text: 'Ji bilkul. Kal subah 10 baje ya shaam 5 baje — kaunsa samay theek rahega?' },
        { role: 'caller', text: 'Shaam 5 baje.' },
        { role: 'ai', text: 'Ho gaya — kal shaam 5 baje book kar diya. Aapko WhatsApp par confirmation bhej rahi hoon.' },
      ];
    }
    return [
      { role: 'ai', text: `Namaste! ${nameOf(call.owner_phone)}.` },
      { role: 'caller', text: 'Kya aap kal khule hain?' },
      { role: 'ai', text: 'Ji haan, kal subah 9 se shaam 7 tak. Main aapka message doctor ko bhej doongi.' },
    ];
  }, [call]);

  return (
    <AnimatePresence>
      {call && (
        <>
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-[80] bg-black/60 backdrop-blur-sm"
          />
          <motion.aside
            initial={{ x: '100%' }} animate={{ x: 0 }} exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 320 }}
            className="fixed right-0 top-0 z-[85] flex h-full w-full max-w-md flex-col border-l border-cyan-500/25 bg-slate-950/95 backdrop-blur-xl"
          >
            <div className="flex items-center gap-3 border-b border-slate-800 px-5 py-4">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/12">
                <Phone className="h-4 w-4 text-cyan-400" />
              </div>
              <div className="flex-1">
                <div className="font-mono text-sm font-semibold text-white">{fmtPhone(call.caller_phone)}</div>
                <div className="font-mono text-[10px] text-slate-500">{call.id}</div>
              </div>
              <button onClick={onClose} className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-800 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 space-y-5 overflow-y-auto p-5">
              <div className="grid grid-cols-2 gap-3">
                {[
                  { k: 'Outcome', v: <OutcomeChip outcome={call.outcome} /> },
                  { k: 'Duration', v: <span className="font-mono text-sm text-slate-200">{fmtDur(call.duration_sec)}</span> },
                  { k: 'Language', v: <span className="text-sm text-slate-200">{call.language}</span> },
                  { k: 'Started', v: <span className="font-mono text-xs text-slate-400">{fmtAgo(call.started_at)}</span> },
                  { k: 'Clinic', v: <span className="text-sm text-slate-200">{nameOf(call.owner_phone)}</span> },
                  { k: 'Owner line', v: <span className="font-mono text-xs text-slate-400">{fmtPhone(call.owner_phone)}</span> },
                ].map((row) => (
                  <div key={row.k} className="rounded-xl border border-slate-800 bg-slate-900/50 p-3">
                    <div className="mb-1 text-[10px] uppercase tracking-[0.15em] text-slate-500">{row.k}</div>
                    {row.v}
                  </div>
                ))}
              </div>

              <div>
                <div className="mb-3 flex items-center gap-2">
                  <Mic className="h-3.5 w-3.5 text-cyan-400" />
                  <h3 className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">Transcript</h3>
                </div>
                <div className="space-y-3">
                  {script.map((m, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07 }}
                      className={`flex ${m.role === 'ai' ? 'justify-start' : 'justify-end'}`}
                    >
                      <div className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed ${
                        m.role === 'ai'
                          ? 'rounded-tl-sm border border-cyan-500/20 bg-cyan-500/10 text-slate-200'
                          : 'rounded-tr-sm border border-slate-700 bg-slate-800/70 text-slate-300'
                      }`}>
                        <div className={`mb-1 font-mono text-[9px] uppercase tracking-wider ${
                          m.role === 'ai' ? 'text-cyan-400' : 'text-slate-500'
                        }`}>
                          {m.role === 'ai' ? 'receptionist' : 'caller'}
                        </div>
                        {m.text}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
                <div className="mb-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.15em] text-slate-500">
                  <Volume2 className="h-3 w-3" /> Recording
                </div>
                <div className="flex items-center gap-3">
                  <button className="flex h-9 w-9 items-center justify-center rounded-full bg-cyan-500/15 text-cyan-400 transition hover:bg-cyan-500/25">
                    <Play className="h-3.5 w-3.5" />
                  </button>
                  <div className="flex h-8 flex-1 items-end gap-0.5">
                    {Array.from({ length: 46 }).map((_, i) => (
                      <motion.span
                        key={i}
                        animate={{ height: [`${8 + Math.random() * 60}%`, `${8 + Math.random() * 60}%`] }}
                        transition={{ duration: 1.4 + Math.random(), repeat: Infinity, repeatType: 'reverse' }}
                        className="w-full rounded-sm bg-cyan-500/35"
                      />
                    ))}
                  </div>
                  <span className="font-mono text-[10px] text-slate-500">{fmtDur(call.duration_sec)}</span>
                </div>
              </div>
            </div>

            <div className="flex gap-2 border-t border-slate-800 p-4">
              <button
                onClick={() => { navigator.clipboard?.writeText(call.id); setCopied(true); setTimeout(() => setCopied(false), 1400); }}
                className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-900 py-2.5 text-xs font-medium text-slate-300 transition hover:bg-slate-800"
              >
                {copied ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                {copied ? 'Copied' : 'Copy ID'}
              </button>
              <button className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-cyan-500 py-2.5 text-xs font-semibold text-slate-950 transition hover:bg-cyan-400">
                <ExternalLink className="h-3.5 w-3.5" /> Open clinic
              </button>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
