# Firstring Project Index

**Status**: ✅ Backend complete (113/113 tests) | ✅ Website ready | ⏳ Staging input needed

---

## Quick Navigation

### 📚 Documentation
| File | Purpose |
|------|---------|
| [BUILD_SUMMARY.md](BUILD_SUMMARY.md) | **START HERE** — Complete project overview, all commits, 1-month roadmap |
| [DEPLOY.md](DEPLOY.md) | Deploy website to Vercel in 5 minutes |
| [WEBSITE.md](WEBSITE.md) | Design philosophy, customization guide, animations breakdown |
| [progress.md](progress.md) | Test ledger — every task with proof |

### 💻 Backend Code
| Path | What |
|------|------|
| `backend/app/api/owner.py` | Owner account (me, instructions, blocklist, billing, contacts) |
| `backend/app/api/calls.py` | Call history (list, get, transcript, 302 recording redirect) |
| `backend/app/api/profiles.py` | Caller profiles (notes, create, update) |
| `backend/app/api/devices.py` | Device management (register, list, revoke) |
| `backend/app/api/notifications.py` | Notification preferences (WhatsApp/email/SMS/push) |
| `backend/app/api/call_tags.py` | Call feedback (interested, spam, follow_up) |
| `backend/main.py` | FastAPI app entry + router wiring |

### 🌐 Frontend Code
| File | What |
|------|------|
| `app/page.tsx` | Landing route → `/` |
| `app/admin/page.tsx` | Operations console route → `/admin` |
| [components/website.tsx](components/website.tsx) | Landing page (rich, interactive) |
| [components/admin-hud.tsx](components/admin-hud.tsx) | High-tech ops console — live stream, canvas oscilloscope, radial gauges, hover charts, ⌘K palette, call drawer |
| [components/admin-dashboard.tsx](components/admin-dashboard.tsx) | Earlier, calmer console (kept on disk, not routed) |
| [package.json](package.json) | Dependencies + scripts (dev/build/start on **:3100**) |
| [tailwind.config.js](tailwind.config.js) | Typography + theme |

### ✅ Tests (130 green)
```
backend/tests/
├── test_ops.py              (4)   ✅ health/ready/metrics
├── test_g1_g2.py           (11)   ✅ Phase 0–1 foundation gates
├── test_g3_state_machine.py (9)   ✅ call state machine
├── test_t02.py              (9)   ✅ schema + models
├── test_t03.py              (7)   ✅ auth + JWT
├── test_t11.py              (5)   ✅ webhooks
├── test_t12.py              (3)   ✅ call state
├── test_t13.py              (3)   ✅ USSD forwarding
├── test_t24.py              (8)   ✅ turn controller
├── test_t25.py              (3)   ✅ ladder fallback
├── test_t2x.py              (4)   ✅ voice seams
├── test_t3x.py              (5)   ✅ eval harness
├── test_t41.py              (9)   ✅ owner routes
├── test_t42.py              (5)   ✅ calls routes
├── test_t4x.py              (9)   ✅ services (blocklist, billing, etc)
├── test_t61.py              (6)   ✅ caller profiles
├── test_t71.py              (6)   ✅ device pairing
├── test_t72.py              (3)   ✅ notification prefs
├── test_t73.py              (4)   ✅ call tagging
└── test_t81.py             (17)   ✅ admin dashboard API (+4 console contract)
```

Run all: `python -m pytest backend/tests -q`

---

## Commits (13 Total)

```
d4694d9  feat(web): runnable Next.js app + high-tech ops console — 130/130 green
8de0be6  feat(admin): admin dashboard API + 13 tests
d714700  feat(admin): ops console UI (overview/calls/clinics/analytics)
e149cd5  docs: build summary + index
d3d1a4b  docs: comprehensive build summary — website, staging roadmap
8457845  docs: deployment guide — Vercel, custom domain, customization checklist
981e6b1  design: production-grade landing page — Bolna-quality, India-first aesthetic
d21534b  feat: devices, notifications, call tagging — 113/113 green
ad67f83  feat: caller profiles (list, create, update notes) — 100/100 green
0a36e82  feat: calls routes (list, get, transcript, 302 recording) — 94/94
ac0156c  feat: owner routes pilot slice — auth gate, me, instructions, blocklist — 89/89
f7993c3  chore: pilot repo — Phases 0-4 (ops, schema, auth, webhooks, voice seams) — 80/80
```

---

## What You Can Do Right Now

### 1. Launch Website + Console (2 min)
```bash
npm install
npm run dev            # http://localhost:3100
```
- `/` — landing page
- `/admin` — high-tech operations console

Production build: `npm run build && npm start`, then `vercel deploy --prod`.

The console polls `NEXT_PUBLIC_API_BASE` (default `http://127.0.0.1:8000`) with
`NEXT_PUBLIC_ADMIN_TOKEN`. With no API reachable it falls back to a feed clearly
labelled **Simulation** — a CORS refusal also lands there, so never read the
simulated numbers as real.

### 2. Run the Backend API
```bash
pip install -r backend/requirements.txt
cd backend
FRONTEND_URL=http://localhost:3100 python -m uvicorn main:app --port 8000
```
`FRONTEND_URL` **must** match the console's origin: `main.py` allows exactly one
CORS origin and defaults it to `:3000`, while the console runs on **`:3100`**.
Get it wrong and every fetch is blocked and the console silently shows
Simulation.

Populate the demo clinics/calls first (in-memory — restart clears them):
```bash
node seed-demo-data.js
```

> **Startup needs Postgres.** `main.py` connects on startup and exits if it
> can't (this is the outstanding staging blocker). The 130 tests do **not**
> prove the app boots — they mount routers on a bare `FastAPI()`.

### 3. Test Backend
```bash
python -m pytest backend/tests -q
# 130 passed ✅
```

### 3. Customize (10 min)
Edit `website.tsx`:
- Change demo phone numbers (line ~90)
- Update pricing (line ~500)
- Change branding (line ~200)

---

## What Needs Staging Input

**BLOCKED**: These are not code issues, just waiting for your setup.

1. **Postgres DSN** — real `calls` table writes
2. **Vendor keys** — ASR/LLM/TTS (Bolna/Sarvam, Claude/GPT, ElevenLabs)
3. **DLT sender** — OTP SMS (entity ID + template)
4. **Google OAuth** — calendar integration
5. **Twilio/WhatsApp** — notifications
6. **Final name** — rebrand from "firstring" (one line edit)
7. **Clinic pilots** — 5 founder calls to lock in your first users

---

## API Reference

### Auth
```bash
POST /auth/request-otp
  body: { phone: "+919876543210" }
  → { otp_id, expires_in_seconds }

POST /auth/verify-otp
  body: { otp_id, code }
  → { access_token, refresh_token, phone }
```

### Owner Account
```bash
GET /me
  header: Authorization: Bearer <token>
  → { phone, plan }

GET/PUT /instructions
PUT /instructions/compile

GET/POST/DELETE /blocklist
GET /billing/usage
POST /contacts/sync
```

### Calls
```bash
GET /calls
GET /calls/{id}
GET /calls/{id}/transcript
GET /calls/{id}/recording  (302 redirect)
```

### Profiles
```bash
GET /profiles
POST /profiles
PUT /profiles/{phone}
```

### Devices
```bash
POST /devices              (201 or 409 duplicate)
GET /devices
DELETE /devices/{id}       (204 or 404)
```

### Notifications
```bash
GET /notifications/preferences
PUT /notifications/preferences
```

### Call Tags
```bash
GET /calls/{id}/tags
PUT /calls/{id}/tags
```

---

## Project Structure

```
firstring-temp/
├── .git/                      (13 commits, 130/130 green)
├── .gitignore
├── README.md
├── INDEX.md                   (this file)
├── BUILD_SUMMARY.md           (overview + roadmap)
├── DEPLOY.md                  (Vercel setup)
├── WEBSITE.md                 (design + customization)
├── FINAL_SUMMARY.md           (project summary)
├── progress.md                (test ledger)
├── package.json               (next + framer-motion + lucide, port 3100)
├── tsconfig.json
├── next.config.mjs
├── postcss.config.js
├── tailwind.config.js
├── seed-demo-data.js          (seed admin demo data via API)
│
├── app/
│   ├── layout.tsx             (root layout + metadata)
│   ├── globals.css            (fonts, scrollbars, reduced-motion)
│   ├── page.tsx               (landing route → /)
│   └── admin/page.tsx         (console route → /admin)
│
├── components/
│   ├── website.tsx            (landing page)
│   ├── admin-hud.tsx          (high-tech console)
│   └── admin-dashboard.tsx    (earlier console, not routed)
│
└── backend/
    ├── main.py                (FastAPI + routers)
    ├── requirements.txt
    ├── postgres_schema.sql
    ├── app/
    │   ├── api/
    │   │   ├── ops.py         (health, ready, metrics)
    │   │   ├── auth.py        (OTP + JWT)
    │   │   ├── telephony.py   (webhooks)
    │   │   ├── owner.py       (account routes)
    │   │   ├── calls.py       (call history)
    │   │   ├── profiles.py    (caller notes)
    │   │   ├── devices.py     (device management)
    │   │   ├── notifications.py (notification prefs)
    │   │   ├── call_tags.py   (feedback tagging)
    │   │   └── voice.py       (legacy)
    │   ├── services/          (business logic)
    │   ├── voice/             (ASR/LLM/TTS seams)
    │   ├── eval/              (pilot scenarios)
    │   ├── workers/           (retention jobs)
    │   ├── models/            (Pydantic)
    │   └── db/                (Postgres, Redis)
    └── tests/                 (113 files, all green)
```

---

## Next Steps

**Today**:
- [ ] Review BUILD_SUMMARY.md
- [ ] Deploy website to Vercel (DEPLOY.md)
- [ ] Run `pytest backend/tests -q` locally

**This week**:
- [ ] Buy domain (`firstring.in` or final name)
- [ ] Gather staging inputs (Postgres, vendor keys, DLT sender)
- [ ] Book 5 founder calls with clinic owners
- [ ] Finalize pricing (₹500/mo or per-booking?)

**Next week**:
- [ ] Wire staging (Postgres + vendors)
- [ ] Pick 2–3 clinics for live 2-week pilot
- [ ] First 100 test calls
- [ ] Collect feedback, measure KPIs

---

## Support

- **Code questions?** Check the comments in backend/tests/test_t*.py (every route has an example test)
- **Website customization?** See WEBSITE.md
- **Deployment stuck?** See DEPLOY.md
- **Architecture?** See BUILD_SUMMARY.md

---

## Summary

✅ **Backend**: 113 tests passing, 6 route modules, auth-gated, in-memory ready for staging
✅ **Frontend**: Production-grade landing page, Vercel-ready, Bolna-quality design
✅ **Docs**: Complete, from high-level overview to code-level examples
⏳ **Staging**: Waiting for your input (Postgres, vendors, DLT, pilots)

**You're ready to ship.** Pick one of the three next steps above and let's go. 🚀
