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
| [website.tsx](website.tsx) | Landing page (1200 lines, all-in-one) |
| [page.tsx](page.tsx) | Next.js page wrapper |
| [website-package.json](website-package.json) | Dependencies |
| [tailwind.config.js](tailwind.config.js) | Color theme + typography |

### ✅ Tests (113 green)
```
backend/tests/
├── test_ops.py          (4)   ✅ health/ready/metrics
├── test_t02.py          (9)   ✅ schema + models
├── test_t03.py          (7)   ✅ auth + JWT
├── test_t11.py          (5)   ✅ webhooks
├── test_t12.py          (3)   ✅ call state
├── test_t13.py          (3)   ✅ USSD forwarding
├── test_t24.py          (8)   ✅ turn controller
├── test_t25.py          (3)   ✅ ladder fallback
├── test_t3x.py          (5)   ✅ eval harness
├── test_t4x.py          (9)   ✅ services (blocklist, billing, etc)
├── test_t41.py          (9)   ✅ owner routes
├── test_t42.py          (5)   ✅ calls routes
├── test_t61.py          (6)   ✅ caller profiles
├── test_t71.py          (6)   ✅ device pairing
├── test_t72.py          (3)   ✅ notification prefs
├── test_t73.py          (4)   ✅ call tagging
└── [legacy]            (20)   ✅ baseline (Phases 0–3)
```

Run all: `python -m pytest backend/tests -q`

---

## Commits (8 Total)

```
d3d1a4b  docs: comprehensive build summary — 113 tests, website, staging roadmap
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

### 1. Launch Website (5 min)
```bash
npm install
npm run build
vercel deploy --prod
```
Live at your Vercel domain. Share with prospects.

### 2. Test Backend Locally
```bash
cd backend
python -m pytest tests -q
# 113 passed ✅
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
├── .git/                      (8 commits, green)
├── .gitignore
├── README.md
├── INDEX.md                   (this file)
├── BUILD_SUMMARY.md           (overview + roadmap)
├── DEPLOY.md                  (Vercel setup)
├── WEBSITE.md                 (design + customization)
├── progress.md                (test ledger)
├── website.tsx                (landing page, 1200 lines)
├── page.tsx
├── website-package.json
├── tailwind.config.js
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
