# firstring-temp — TEMP NAME, do not brand yet

> All `.com`/`.ai` candidates checked 2026-10-12 are taken. This folder keeps
> a temp name until the trademark + domain check passes. See plan docs for shortlist.

## Ruling: reuse, don't re-scaffold

`../MediCall-AI` already implements this project's stack (LiveKit Agents,
FastAPI backend with `app/` + `tests/`, Next.js frontend, PG + pgvector).
A parallel scaffold would be a duplicate codebase. So this folder holds
only the **pilot thin slice**; the build base is MediCall-AI.

- Base: `../MediCall-AI/backend` (Python/FastAPI) + `../MediCall-AI/frontend`
- Pilot scope: 3-clinic after-hours receptionist, per-booking pricing
- Pipeline for pilot: keep MediCall-AI's LiveKit base; Bolna (MIT) stays
  the fallback if vendor bills exceed the ₹5,000 pilot budget

## Pilot go / no-go (measure before any §A–§D build-out)

- GO: ≥60% of after-hours calls answered, ≥1 booking captured per clinic
  per week, ≥1 clinic agrees to paid per-booking terms
- NO-GO: anything less — kill the pilot, keep the docs

## Next commands (run from MediCall-AI, not here)

```powershell
cd "C:\Users\vigilare\OneDrive - Vigilare BP PVT LTD\Documents\MediCall-AI"
python -m pytest backend/tests -q
```

## Open items (need owner answers)

1. Final name (Answered / FirstRing replacement) + `.in` + TM class 9/38/42
2. Pilot vertical + city (suggest dental, Hyderabad)
3. Language for any new service: match base (Python) unless a step says otherwise
