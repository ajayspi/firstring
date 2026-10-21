# firstring-temp — TEMP NAME, do not brand yet

> All `.com`/`.ai` candidates checked 2026-10-12 are taken; FirstRing is
> rejected (3/3 domains + FirstRing India Pvt Ltd exists). Name TBD.

**Status: pilot scaffold. Nothing is deployed and no call has ever been placed.**
All vendors, the database and telephony are wired as seams behind tests, not as
working integrations. Read the [verification notes](FINAL_SUMMARY.md) before
believing any number here.

## What this is

An **SMB after-hours AI receptionist** for India: a clinic/salon forwards
its calls here; we answer in Hindi or English, book into the real
calendar, and WhatsApp the owner. Sold per booking. (Consumer Equal-AI
competitor premise is dead — research: that category earns <$5k/month.)

## Layout

```
backend/            FastAPI + LiveKit + PG/pgvector (copied from MediCall-AI 2026-10-12)
  app/api/          ops, auth, telephony (signed webhooks), voice, owner, calls,
                    profiles, devices, notifications, call_tags, admin
  app/services/     auth, webhooks, call_state, forwarding, blocklist,
                    prompts, billing, contacts
  app/voice/        asr, llm, tts seams + turn controller + fallback ladder
  app/eval/         pilot scenarios + scorer
  app/workers/      retention windows
  tests/            20 files, 130 tests
  Dockerfile        container entrypoint (uvicorn main:app)
app/                Next.js routes — / (landing) and /admin (ops console)
components/         website.tsx, admin-hud.tsx (ops console)
progress.md         SDD ledger — every task line carries its test evidence
```

MediCall-AI is history: copied, not moved; its files stay as they were.

## Run

```powershell
cd "C:\Users\vigilare\OneDrive - Vigilare BP PVT LTD\Documents\firstring-temp"
python -m pytest backend/tests -q      # expect 130 passed
npm install && npm run dev             # :3100  →  /  and  /admin
```

The green suite pins route behaviour; it mounts routers on a bare `FastAPI()`, so
**it does not prove `main.py` boots**. Booting needs Postgres (`DATABASE_URL`).

> **This repo is public.** The admin tokens in the source are throwaway demo
> values and the API must never be hosted on them. Set real secrets in the
> environment instead: `ADMIN_TOKEN`, `FOUNDER_TOKEN`, `DATABASE_URL`,
> `FRONTEND_URL`.

## Pilot go / no-go (measure before any further build-out)

- GO: ≥60% of after-hours calls answered, ≥1 booking captured per clinic
  per week, ≥1 clinic agrees to paid per-booking terms
- NO-GO: anything less — kill the pilot, keep the docs

## Open items (owner input needed)

1. Final name + `.in`/TM class 9/38/42 check
2. Pricing: per-booking ₹50 (recommended) vs ₹10/week (loses ~₹3,200/yr
   per business at current cost structure — see chat)
3. Staging: Postgres + vendor keys → unblocks migrations, HTTP routes,
   first real call, vendor bake-off
4. DLT sender (entity + header + OTP template) → unblocks real OTP SMS
