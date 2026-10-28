# PROGRESS.md — PrognosIQ source of truth

> Maintained by @Proudly95 + AI pair (Z.ai chat) + Claude Code (VS Code).
> Rule: every session starts by reading this file. Update it BEFORE ending a session.
> Last updated: 2026-10-28 — rewritten from a VERIFIED repo brief by Claude Code.

## Product vision (the real endgame)

Simulated industrial machines stream telemetry over MQTT/OPC-UA → ML models
(NASA C-MAPSS dataset) predict Remaining Useful Life (RUL) → failing assets
auto-generate maintenance work orders → live dashboard.
Target stack: FastAPI + PostgreSQL/TimescaleDB · Next.js/TS frontend ·
scikit-learn → PyTorch LSTM/1D-CNN (MLflow + DVC) · Mosquitto MQTT + asyncua
OPC-UA (Kafka in Phase 5) · Docker, GitHub Actions, Prometheus/Grafana, Evidently.

## Verified repo state (2026-10-28)

- Monorepo, uv-managed. Only `apps/api` has real code;
  `apps/web`, `services/ml`, `services/simulator` = placeholder READMEs.
- Routers: `app/api/routes/` — auth.py, orgs.py, assets.py
- Models: `app/models/` — User, Organization, OrganizationMember, Asset,
  WorkOrder (+ enums)
- Auth: JWT access 15 min + refresh 7 days, bcrypt registration
- Roles: **admin / viewer / agent** (NOT "member" — earlier notes were wrong)
- Tests: 22 passing; conftest self-heals `prognosiq_test` (fails if server down)
- Infra: docker-compose, Postgres 127.0.0.1:5432, container `prognosiq-db-1`,
  Docker Desktop (Windows) must be running first
- Dev workflow: `.venv/bin/python` (no bare `python` on PATH) · tests:
  `cd apps/api && /home/dev/prognosiq/.venv/bin/python -m pytest -q` ·
  server: `uv run uvicorn app.main:app --reload`

## Git state

- Branch `feat/orgs-rbac`. Recent commits: JWT login (#22) → orgs + RBAC →
  self-healing test DB + compose hardening → invalid-role 422 test fix
- ⚠️ UNCOMMITTED working tree = assets CRUD, essentially complete:
  - NEW `app/api/routes/assets.py` — full CRUD under `/orgs/{org_id}/assets`
    (list paginated, create 201, get, patch, delete 204)
  - NEW `app/schemas/asset.py` — AssetCreate / AssetUpdate / AssetOut / AssetPage
  - NEW `app/core/pagination.py` — generic PageParams dependency (page/size → offset/limit)
  - NEW `tests/test_assets.py` — 8 tests (RBAC outsider/viewer/agent/admin,
    invalid type 422, pagination, org scoping)
  - EDIT main.py (router at `/orgs` prefix), config.py (database_url_test),
    models/asset.py (Text/relationship imports)
- → FIRST ACTION: commit this work before starting anything new.

## Next task: maintenance records

- `models/asset.py` imports relationship/Text but NO MaintenanceRecord model
  exists yet; `models/__init__.py` doesn't export one
- ⚠️ TRAP: migration `3c9cdc0412e8_add_maintenance_records.py` (revises
  `dacd6c6f094c`) is an EMPTY STUB — upgrade()/downgrade() are `pass`.
  Looks done, creates nothing. Silent no-op.
- No schemas/routes/tests for maintenance records yet
- Plan: MaintenanceRecord model (FK→assets + Asset relationship) →
  export in `models/__init__.py` → fill the stub (keeps revision chain) or
  delete + regenerate (then re-stamp) → schemas/routes/tests → commit

## AI/ML scope (lives in `services/ml` — currently a placeholder README)

- Dataset: NASA C-MAPSS turbofan degradation (FD001–FD004) → predict RUL
- Track: sklearn baseline first → PyTorch LSTM / 1D-CNN on sensor sequences
- Tooling: MLflow (runs + model registry), DVC (dataset/model versioning),
  Evidently (drift monitoring), Prometheus/Grafana (serving metrics)
- Integration: RUL below threshold → auto-generate WorkOrder via API
- Can start NOW with the static C-MAPSS files; live telemetry only needed
  after #11/#12 exist
- Suggested new tickets: ML-1 data pipeline+EDA, ML-2 sklearn baseline+MLflow,
  ML-3 LSTM/1D-CNN+DVC, ML-4 prediction endpoint, ML-5 auto-workorder hook

## Real names (verified — no guessing)

- Roles: admin / viewer / agent
- Route files: `app/api/routes/{auth,orgs,assets}.py`
- Asset schemas: `app/schemas/asset.py`
- Pagination: `app/core/pagination.py` → PageParams
- Test DB: `prognosiq_test` · dev DB container: `prognosiq-db-1`
- Auth dependency: **`get_current_user`** — defined in `app/api/routes/auth.py`
- DB session dependency: **`get_db`** — `app/core/db.py`, returns `Iterator[Session]`
- Org member / RBAC dependency: **`get_current_org_member`** — `app/api/routes/orgs.py`
  (the gatekeeper every `/orgs/{org_id}/...` route uses for role checks)
- Router registration: `app/main.py`, assets router at prefix `/orgs`
- Member FK field: [OPEN — need `app/models/organization_member.py`]
- Asset model fields: [OPEN — need `app/models/asset.py`]

## Rules

1. Never code from memory — real names pasted first, then adapt.
2. Test suite stays green.
3. Branch → commit → PR ("Closes #N" in body).
4. Read this file at session start; update it at session end.

## Board (@Proudly95's PrognosIQ GitHub Project)

- Done: #1 skeleton, #2 docker compose, #3 models+Alembic, #4 registration,
  #5 JWT login, #6 orgs+RBAC, #10 ADR-0001
- In progress: #7 Assets CRUD + pagination
- Backlog: #8 work orders CRUD, #9 pytest+CI job (partially done),
  #11 SimulatorL OPC-UA, #12 collectors + MQTT bridge, #13 dual-protocol ADR

## Security / gotchas

- `secret_key` is still the dev placeholder ("change-me") — MUST rotate
  before any deployment (pre-production flag)
- Empty migration stub = silent no-op trap
- Bare `python` not on PATH — always `.venv/bin/python` or `uv run`
