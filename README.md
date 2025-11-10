# GHMS v3 — Government Hospital Management System

End-to-end Django-based hospital management and accountability platform built for public/government facilities.

This implementation matches the hackathon proposal:

- Unified EHR + departmental workflows (OPD, Lab, Radiology, Pharmacy, Finance)
- Strong RBAC so each role only sees its department data
- AI-powered Doctor Activity Audit System (DAAS) for shift verification
- Cryptographic audit logging with hash-chaining and SIEM export
- JWT-secured DRF API with OIDC-ready hooks
- Optional Postgres RLS / WORM semantics for immutable audit storage

---

## 1. Features Overview

### Core Governance & Security
- **RBAC** via `core` app & middleware: DOCTOR, NURSE, LAB_TECH, RADIOLOGIST, PHARMACY, FINANCE, AUDITOR.
- **Department scoping**: users only access patients & workflows assigned to their department.
- **JWT auth** (SimpleJWT) + session auth for web.
- **OIDC placeholders** to integrate with national e-ID / SSO.
- **Audit hash-chain**:
  - `audit.utils.log()` writes `AuditLog` rows with `prev_hash` + `hash`.
  - Exports each event to NDJSON for SIEM ingestion.
  - Sample SQL in `audit/migrations.sql` shows how to enable Postgres RLS + append-only behavior.

### Doctor Activity Audit System (DAAS)
- `/daas/ingest/` endpoint secured by `X-DAAS-TOKEN`.
- Accepts telemetry: `username`, `action`, `upi`, `host`, and `meta` (keystrokes, mouse moves, active window, duration, etc).
- Lightweight AI-style scoring in Python:
  - Calculates an **Engagement Score (0–100)** per event.
  - Rewards clinical-system activity & real input.
  - Penalizes idle/suspicious patterns.
- Persists:
  - Raw events in `DaasEvent`.
  - Aggregated signals in `ActivityEvidence` with human-readable reasons.
- `daas.logic.compute_shift_verified()`:
  - Aggregates scores per 8-hour block.
  - Marks shift **VERIFIED** when cumulative score ≥ 75.

### Clinical & Workflow
- `patients`: registration + search via UPI / National ID / phone (with OTP rate limiting).
- `workflow`: cross-department referrals with full audit trail.
- `clinical`: Lab, Radiology, Pharmacy, Finance models linked to patients and audit.
- `ui`: simple PicoCSS dashboard:
  - Department worklists
  - DAAS verification summary
  - Recent audit entries

### API
Key DRF endpoints exposed under `/api/`:
- `/api/patients/`, `/api/referrals/`
- `/api/lab/orders/`, `/api/lab/results/`
- `/api/rad/orders/`, `/api/rad/studies/`
- `/api/invoice/`, `/api/payment/`
All protected by JWT + RBAC.

---

## 2. Quickstart (Dev, SQLite)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd ghms
python manage.py migrate
python manage.py createsuperuser  # optional
python manage.py seed_demo        # if provided in this repo
python manage.py runserver 0.0.0.0:8000
```

Then open: `http://127.0.0.1:8000`

### Demo Users

- `admin` / `Admin123!`
- `opd_doc` / `Passw0rd!`
- `lab_tech` / `Passw0rd!`
- `radiology_user` / `Passw0rd!`
- `pharmacy_user` / `Passw0rd!`
- `finance_user` / `Passw0rd!`
- `nurse_user` / `Passw0rd!`

> Note: change passwords + `DJANGO_SECRET_KEY` + `DAAS_TRUSTED_TOKENS` in production.

---

## 3. DAAS Agent Example

Example payload to send from a workstation agent:

```bash
curl -X POST http://localhost:8000/daas/ingest/ \
  -H "Content-Type: application/json" \
  -H "X-DAAS-TOKEN: demo-token-123" \
  -d '{
        "username": "opd_doc",
        "action": "ehr_active",
        "upi": "UPI12345",
        "host": "OPD-TERM-01",
        "meta": {
          "keystrokes": 54,
          "mouse_moves": 80,
          "active_window": "GHMS-EHR",
          "duration_sec": 60
        }
      }'
```

The response includes `engagement_score` and `reason`, and evidence is added to shift verification.

---

## 4. Postgres RLS & WORM

To align with immutable-audit promises:
- Use PostgreSQL in production.
- Apply the sample SQL policies in `audit/migrations.sql`:
  - Limit direct writes.
  - Enforce append-only semantics for `audit_auditlog`.
  - Route reads through service roles.

This codebase is now aligned with the hackathon proposal: runnable, secure, and demonstrably AI-augmented for doctor accountability and hospital transparency.
