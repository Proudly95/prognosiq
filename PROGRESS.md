# PROGRESS.md — PrognosIQ source of truth

> Maintained by @Proudly95 + AI pair (Z.ai chat) + Claude Code (VS Code).
> Rule: every session starts by reading this file. Update it BEFORE ending a session.
> Last updated: 2026-11-03 — #8 work orders CRUD built (10 new tests,
> 50/50 green, PR pending merge); next task: #9 CI test job.

## Product vision (the real endgame)

Simulated industrial machines stream telemetry over MQTT/OPC-UA → ML models
(NASA C-MAPSS dataset) predict Remaining Useful Life (RUL) → failing assets
auto-generate maintenance work orders → live dashboard.
Target stack: FastAPI + PostgreSQL/TimescaleDB · Next.js/TS frontend ·
scikit-learn → PyTorch LSTM/1D-CNN (MLflow + DVC) · Mosquitto MQTT + asyncua
OPC-UA (Kafka in Phase 5) · Docker, GitHub Actions, Prometheus/Grafana, Evidently.

## Verified repo state (2026-11-03)

- Monorepo, uv-managed. Only `apps/api` has real code;
  `apps/web`, `services/ml`, `services/simulator` = placeholder READMEs.
- Routers: `app/api/routes/` — auth.py, orgs.py, assets.py,
  maintenance_records.py (assets + maint registered at `/orgs` prefix)
- Models: `app/models/` — User, Organization, OrganizationMember, Asset,
  WorkOrder, MaintenanceRecord (+ enums)
- Auth: JWT access 15 min + refresh 7 days, bcrypt registration
- Roles: **admin / viewer / agent** (NOT "member" — earlier notes were wrong)
- Tests: **40/40 passing** (verified 2026-11-03). Per-file breakdown verified
  via `pytest --collect-only`: test_auth 11 · test_orgs 10 · test_assets 8 ·
  test_maintenance_records 9 · test_health 2. The 22→40 growth is the new
  asset + maintenance-record suites. conftest self-heals `prognosiq_test`
  (fails if server down)
- Infra: docker-compose, Postgres 127.0.0.1:5432, container `prognosiq-db-1`,
  Docker Desktop (Windows) must be running first
- Dev workflow: `.venv/bin/python` (no bare `python` on PATH) · tests:
  `cd apps/api && /home/dev/prognosiq/.venv/bin/python -m pytest -q` ·
  server: `uv run uvicorn app.main:app --reload` ·
  lint (every commit, Rule 8): `.venv/bin/ruff check --fix apps/api &&
  .venv/bin/ruff format apps/api` from repo root

## Git state

- 2026-11-03: PR #33 squash-merged into main — ALL of it: assets CRUD,
  maintenance records, pagination, migration, tests, PROGRESS.md + README.
  Local `main` synced to 293167a; suite green (40/40) at merge.
- `feat/orgs-rbac` fully merged — parity with main verified (empty diff).
  Safe to delete: `git branch -d feat/orgs-rbac` +
  `git push origin --delete feat/orgs-rbac`.
- Working tree clean, no pending work. Next work = new branch off updated main.
- Workflow from now on: branch → lint (Rule 8) → code → pytest → commit →
  PR → squash-merge (established pattern: #27, #33). CLAUDE.md (repo root,
  created 2026-11-03) is auto-loaded every session and directs the AI to
  this file first.

## Next task: CI test job (#9)

- Create `.github/workflows/ci.yml`: push + PR triggers, postgres:17 service
  container, env matching `database_url_test`, uv-based install,
  `python -m pytest -q` in apps/api, README badge, green checks on PRs.
- Alembic dependency already present — stale advice corrected (Roadmap #9).

## Last task: work orders CRUD (#8) — BUILT 2026-11-03, 50/50 green (PR pending)

- Org-level routes `/orgs/{org_id}/work-orders` (decided: org-level, not
  asset-nested); `asset_id` + `status` list filters; RBAC mirrors assets
  (viewer read / agent create+update / admin delete); org scoping enforced
  on create too — target asset must be in-org (404), tested.
- ML-5 hook design kept: POST carries no `status` (always starts OPEN) and
  accepts `source` (default manual) — a service account later just POSTs
  with `source=sensor_alert`.
- NEW `app/schemas/work_order.py` · `app/api/routes/work_orders.py` ·
  `tests/test_work_orders.py` (10 tests) · main.py router registration.
- Deferred (fine): maintenance_type enum + performed_by FK review — revisit
  when telemetry/ML design lands.

## Last task: maintenance records — CLOSED 2026-11-03 (merged via #33)

- ✅ Model exists: `models/maintenance_record.py` (MaintenanceRecord), exported
  from `models/__init__.py`; Asset.maintenance_records relationship wired
- ✅ 2026-11-03: MaintenanceRecord model + migration DONE and APPLIED.
  Migration `3c9cdc0412e8` now contains real create_table/create_index
  (filled from the 10-28 draft). Table exists in dev DB; schema verified
  identical to the migration; empty when stamped.
- Incident log (2026-11-03): `alembic upgrade head` failed with
  DuplicateTable — the table pre-existed (ad-hoc `Base.metadata.create_all()`
  against the dev DB) while alembic_version was still at dacd6c6f094c.
  Postgres transactional DDL makes a partial apply impossible, so the table
  had to come from outside Alembic. Fixed with `alembic stamp head`
  (dacd6c6f094c → 3c9cdc0412e8) — lossless, nothing dropped.
  Verified: `alembic current` → 3c9cdc0412e8 (head) · `upgrade head` no-op ·
  40/40 tests green.
- ⚠️ SUPERSEDED: earlier advice to "stamp back to dacd6c6f094c then upgrade"
  was for the MIRROR-IMAGE case (stamp at head, table missing) and is WRONG
  for this repo — it would re-run CREATE TABLE and reproduce DuplicateTable.
- ✅ CLOSED (2026-11-03): routes/schemas/tests all exist — nothing to build.
  `routes/maintenance_records.py` (160 lines, full CRUD, paginated list) ·
  `schemas/maintenance_record.py` · `tests/test_maintenance_records.py`
  (9 tests, 160 lines)
- Left: review enums.py / work_order.py for possible additions
  (maintenance_type enum, performed_by FK); then commit → PR

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
- Route files: `app/api/routes/{auth,orgs,assets,maintenance_records}.py`
- Asset schemas: `app/schemas/asset.py`
- Maintenance records: schemas `app/schemas/maintenance_record.py` ·
  model `app/models/maintenance_record.py` (class MaintenanceRecord) ·
  tests `tests/test_maintenance_records.py` (9) · routes nested at
  `/orgs/{org_id}/assets/{asset_id}/maintenance-records`
- Pagination: `app/core/pagination.py` → PageParams
- SQLAlchemy cross-model relationships (`Mapped["OtherModel"]`) REQUIRE an
  `if TYPE_CHECKING:` import of the referenced model, else ruff F821 false
  positive (wired in asset.py + maintenance_record.py 2026-11-03).
  Ruff runs via `.venv/bin/ruff` or `uv run ruff`; version skew vs the
  pre-commit pin (v0.8.4) is tolerated — rules E/F/I/B/UP/SIM stable
- Test DB: `prognosiq_test` · dev DB container: `prognosiq-db-1`
- Auth dependency: **`get_current_user`** — defined in `app/api/routes/auth.py`
- DB session dependency: **`get_db`** — `app/core/db.py`, returns `Iterator[Session]`
- Org member / RBAC dependency: **`get_current_org_member`** — `app/api/routes/orgs.py`
  (the gatekeeper every `/orgs/{org_id}/...` route uses for role checks)
- Router registration: `app/main.py`, assets router at prefix `/orgs`
- Member model: file is **`app/models/member.py`**, class `OrganizationMember`
  (NO organization_member.py exists — proven by cat error 2026-10-28);
  member FK fields still unverified
- Asset fields (verified): id BigInteger PK · organization_id FK→organizations.id
  (indexed) · name String(255) · asset_type AssetType · serial_number String(255)
  nullable · installed_at DateTime(tz) nullable · is_active bool default True ·
  created_at/updated_at server_default now() + onupdate
- Enums: `app/models/enums.py` (AssetType + `enum_column()` helper)
- asset.py Text import + relationship now USED — Asset.maintenance_records
  back_populates MaintenanceRecord.asset (wired 2026-11-03)

## Rules

1. Never code from memory — real names pasted first, then adapt.
2. Test suite stays green.
3. Branch → commit → PR ("Closes #N" in body).
4. Read this file at session start; update it at session end. Since
   2026-11-03 this is automated: CLAUDE.md (repo root) is auto-loaded every
   Claude Code session and directs the AI here FIRST, then to GitHub
   issues/PRs and apps/*/README.md if the project outgrows this file.
5. Alembic DuplicateTable = schema/version desync. VERIFY FIRST
   (`alembic current` + `\d <table>` in psql), then:
   - existing table MATCHES the migration → `alembic stamp <rev>` FORWARD
   - table missing or differs, data disposable → drop table + `upgrade head`
   - table differs AND holds real data → hand-write ALTER; never drop
   NEVER stamp backward and re-run while the table exists and matches.
6. Dev DB (`prognosiq`) schema changes go through Alembic ONLY — no ad-hoc
   `Base.metadata.create_all()` against it (that caused the 2026-11-03
   desync). `create_all` belongs to `prognosiq_test` / the test suite only.
7. Observe before advising: state checks (`alembic current`, git log, test
   count) come BEFORE any fix instructions. Memory-stale premises caused the
   wrong stamp advice on 2026-11-03.
8. Lint BEFORE every commit (from repo root):
   `~/prognosiq/.venv/bin/ruff check --fix apps/api && ~/prognosiq/.venv/bin/ruff format apps/api`
   Then `git add` any files the fixes touched so they land IN the commit.
   Pre-commit hooks (ruff v0.8.4 + ruff-format + end-of-file/trailing-
   whitespace fixers, config in `.pre-commit-config.yaml` + `pyproject.toml`)
   abort the commit and auto-fix if anything is still dirty — the fix is
   always: re-add the same paths, re-run the same commit. Second attempt
   passes. NEVER use `--no-verify` to skip this.

## Board (@Proudly95's PrognosIQ GitHub Project)

- Done: #1 skeleton, #2 docker compose, #3 models+Alembic, #4 registration,
  #5 JWT login, #6 orgs+RBAC, #7 assets CRUD + pagination (PR #33),
  #10 ADR-0001
- In progress: #8 work orders CRUD — built, 50/50 green, PR pending merge
- Backlog: #9 pytest+CI job (partially done),
  #11 SimulatorL OPC-UA, #12 collectors + MQTT bridge, #13 dual-protocol ADR

## Roadmap (ticket briefs — added 2026-11-03, fact-checked)

Recommended order: #8 → #9 → #13 → #11 → #12 → ML-1…4 (parallelizable
anytime) → ML-5 → dashboard → monitoring. (ML-1/ML-2 need only the static
C-MAPSS files — can start in parallel with anything.)

### #8 — Work orders CRUD + pagination ✅ BUILT 2026-11-03 (suite 50/50)
- Model + table already exist (class WorkOrder, `app/models/work_order.py`;
  `work_orders` table verified in dev DB). The assets pattern, repeated.
- `app/schemas/work_order.py` — WorkOrderCreate / Update / Out / Page ·
  `app/api/routes/work_orders.py` — list / create 201 / get / patch /
  delete 204 under `/orgs/{org_id}/work-orders`
- List filters: `asset_id`, `status` query params
- RBAC via `get_current_org_member`, mirroring assets' role rules
- Org-scoping test mandatory (org B can never see org A's work orders)
- ~10 tests, same mold as `tests/test_assets.py` (RBAC ×3 roles,
  422 invalid enum, pagination, scoping) · suite green ~50 → PR "Closes #8"
- Design POST so a service account can create work orders later
  (ML-5 hook entry point). FIRST STEP: read `work_order.py` — its fields
  and status enums are not yet on record here (Rule #1).

### #9 — pytest setup + CI test job (pytest half DONE)
- DONE: self-healing conftest, 40/40 green.
- REMAINS: `.github/workflows/ci.yml` — push + PR triggers, postgres:17
  service container, env matching `database_url_test`, uv-based install,
  `python -m pytest -q` in apps/api, README badge, green checks on PRs.
- ⚠️ CORRECTION 2026-11-03: alembic is NOT a missing dependency — it is in
  `pyproject.toml` deps + `uv.lock`. Earlier "add alembic to requirements"
  advice was stale; ignore it.

### #13 — ADR-0002: dual-protocol integration (write BEFORE building #11/#12)
- Same format as ADR-0001. Decisions to record: ingestion path (MQTT
  consumer → DB vs API endpoint) · TimescaleDB timing (hypertables for
  telemetry) · payload format (JSON now; protobuf/Avro later?) · what
  triggers the Phase-5 Kafka switch. Link from README when merged.

### #11 — SimulatorL OPC-UA server (`services/simulator/`)
- asyncua server; address space `/Fleet` → machine objects → sensor
  variables; machine types matching the AssetType enum
- Degradation engine: normal telemetry + C-MAPSS-style sensor drift toward
  failure (learnable signal for the ML models)
- Config-driven: machine count, failure modes, sample interval
- Dockerfile + compose entry; endpoint `opc.tcp://…:4840`
- Tests: server boots, tree browsable, values change over time; README
  documents the address-space design. Design the tree with #12/#13 in mind.

### #12 — OPC-UA collectors + MQTT bridge (`services/collector/`) — depends on #11
- asyncua client using subscriptions (not polling); Mosquitto in compose
- Topic scheme + JSON payload contract, e.g.
  `prognosiq/orgs/{org}/assets/{asset}/telemetry`
- Reconnect resilience (survives simulator/broker restarts); tests against
  local OPC-UA + local MQTT; demo: `mosquitto_sub` shows live values for
  every simulated asset. Contract feeds #13's decisions.

### Beyond the board (file tickets when reached)
- Telemetry ingestion + TimescaleDB hypertables (falls out of #13)
- ML track (details in "AI/ML scope"): ML-1 pipeline+EDA · ML-2 sklearn
  baseline+MLflow · ML-3 LSTM/1D-CNN+DVC · ML-4 prediction endpoint ·
  ML-5 auto-workorder hook (needs #8 + ML-4)
- Next.js dashboard (`apps/web`): live RUL + work-order queue
- Monitoring: Prometheus/Grafana + Evidently drift
- ⚠️ Rotate `secret_key` (env-driven, not the change-me placeholder) —
  pre-production blocker (see Security / gotchas)

## Security / gotchas

- `secret_key` is still the dev placeholder ("change-me") — MUST rotate
  before any deployment (pre-production flag)
- (resolved 2026-11-03) The empty-migration-stub trap is fixed and applied —
  see Rules #5–6 for the desync procedure that replaces it
- Bare `python` not on PATH — always `.venv/bin/python` or `uv run`
