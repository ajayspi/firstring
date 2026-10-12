# SDD ledger — plan: C:\Users\vigilare\.opencode\plan\equal-ai-microarchitecture.md (Phases 0–7, pilot-scoped on MediCall-AI base)

Base: copied to this repo 2026-10-12 (`backend/` here; MediCall-AI left as-is). Commit f7993c3 = 80/80 green at move time. All later work happens in THIS repo.
Baseline 2026-10-12: `pytest backend/tests -q` → 20 passed in 1.18s.

Pre-flight (shared interfaces): T1.2 consumes T0.2 (calls/call_events tables); T2.4 consumes T0.2 (voice_configs.turn_policy); T4.x consume T0.3 (JWT auth); T0.4 consumes call_id from T1.2. No conflicts found — base schema is the authority; plan values that contradict the base get a Ruling line.

Ruling: Phase 5 (mobile apps) + Phase 8 (deferred) are out for the pilot (WhatsApp-only owner interface, no app). Cost if wrong: a later app plan.
Ruling: T0.1 CI gate deferred — no git repo exists; `pytest` + eval smoke run locally instead. Cost if wrong: unblocked merges, acceptable pre-repo.
Ruling: T3 bake-off runs against the rented set first (Bolna/Sarvam), not the Deepgram/GPT-4.1/ElevenLabs stack in requirements.txt — pilot budget decides. Cost if wrong: one adapter swap behind the §2.8 seam.

## Phase 0 — Foundations (pilot cut)
- [x] T0.4 observability: /healthz, /readyz, /metrics — Task complete (tests: `pytest backend/tests/test_ops.py` → 4/4 pass; suite 24/24). Files: `backend/app/api/ops.py`, wired in `main.py`.
- [x] T0.2 datastore — Task complete (tests: `pytest backend/tests/test_t02.py` → 9/9 pass). Files: 9 models in `postgres.py`, 9 DDL blocks in `postgres_schema.sql`, `app/workers/retention.py`. Deferred to staging-with-PG (ledgered, not claimed): create_all smoke, migrate/rollback, retention dry-run on real rows.
- [x] T0.3 secrets+auth — Task complete (tests: `pytest backend/tests/test_t03.py` → 7/7 pass; suite 40/40). Files: `app/services/auth.py`, `app/api/auth.py`, wired in `main.py`. Staging still needs: DLT sender wiring, JWT_SECRET rotation schedule doc.

## Phase 1 — Telephony ingress (pilot cut)
- [x] T1.1 webhook receiver — Task complete (tests: `pytest backend/tests/test_t11.py` → 5/5 pass; suite 45/45). Files: `app/services/webhooks.py`, `app/api/telephony.py` (all 3 §C.10 routes), wired in `main.py`. Ruling: initial try + 3 retries (4 calls, sleeps 1/5/25) per §D.2. Pilot cuts: HMAC convention (provider-native schemes on staging), in-memory dedupe/queue (webhook_events UNIQUE + Redis on staging).
- [x] T1.2 — Task complete (tests: `pytest backend/tests/test_t12.py` → 3/3 pass; suite 48/48). File: `app/services/call_state.py` (telephony leg only; base `CallState` consultation leg untouched). Staging still needs: `calls` row creation on webhook + same-write `call_events` append.
- [x] T1.3 forwarding codes — Task complete (tests: `pytest backend/tests/test_t13.py` → 3/3 pass; suite 51/51). File: `app/services/forwarding.py`. Staging still needs: live test-call verification.
- [ ] T1.4 audio bridge — DEFERRED to staging (needs live carrier RTP; nothing unit-testable). Ruling: jitter/loopback accepts run against the first real DID. Cost if wrong: rework of bridge sizing.

## Phase 2 — Voice pipeline (pilot cut)
- [x] T2.1–2.3 adapter seams — Task complete (tests: `pytest backend/tests/test_t2x.py` → 4/4 pass). Files: `app/voice/asr.py`, `app/voice/llm.py`, `app/voice/tts.py`. Real vendors land behind these interfaces on staging; injection refusal by a live LLM is proven by the T7.1 battery, not here.
- [x] T2.4 turn controller — Task complete (tests: `pytest backend/tests/test_t24.py` → 8/8 pass). File: `app/voice/turn.py`; policy keys mirror `voice_configs.turn_policy`.
- [x] T2.5 fallback ladder — Task complete (tests: `pytest backend/tests/test_t25.py` → 3/3 pass; suite 66/66). File: `app/voice/ladder.py`. Gap timing (<2 s) is a staging measurement (T7.2 drills).
- [ ] T2.6 first real call — DEFERRED to staging (needs live DID + vendors).

## Phase 3 — Eval harness (pilot cut)
- [x] T3.1–T3.2 scenarios + scorer — Task complete (tests: `pytest backend/tests/test_t3x.py` → 5/5 pass; suite 71/71). Files: `app/eval/cases.py` (5 pilot scenarios, hi+en), `app/eval/metrics.py`. Staging still needs: seed into `eval_cases`, WER/latency runner (T3.2 full), second-vendor swap (T3.3), measured bake-off (T3.4).

## Phase 4 — Product backend (DB-free slices only)
- [x] T4.x services — 80/80 tests. Files: `app/services/blocklist.py`, `prompts.py`, `billing.py`, `contacts.py`.
- [x] T4.1 owner routes — 89/89 tests (commit ac0156c). File: `app/api/owner.py` — auth gate, GET /me, instructions get/put/compile, blocklist CRUD, billing usage, contacts/sync.
- [x] T4.2 calls routes — 94/94 tests (commit 0a36e82). File: `app/api/calls.py` — list, get, transcript, 302 recording redirect.
- [x] T6.1 caller profiles — 100/100 tests (commit [pending]). File: `app/api/profiles.py` — list, create, update caller notes per owner.
- [ ] T4.3 account routes (DELETE /me, export with job IDs) — SKIPPED (deferred to staging). 202 job queue not implemented; when needed: async worker pattern.
- [ ] T4.4–T4.5 remaining (devices, notifications, device config) — BLOCKED on staging. Not started.
- Ruling: contacts/sync matched-set = `_patients` per owner; staging fills from appointments. GET becomes POST (hashes in body).
- Ruling: repo moved 2026-10-12 → commit f7993c3 baseline 80/80. All further work here.

## Final review
- DEFERRED: whole-branch review fires when the plan's executable portion is complete. Phases 5–7 need staging/live vendors/DLT, so the branch is mid-plan, not finished.
