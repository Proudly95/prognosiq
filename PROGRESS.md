# PROGRESS.md — PrognosIQ source of truth

> Maintained by @Proudly95 + AI pair (Z.ai chat) + Claude Code (VS Code).
> Rule: every session starts by reading this file. Update it BEFORE ending a session.
> Last updated: 2026-11-06 — #11 SimulatorL OPC-UA DONE & MERGED (PR #43 →
> b65e891; issue #11 closed automatically; PR #44 folded the number into
> this file; all stale branches swept). Verified on main 2026-11-06:
> 19 sim + 50 api tests green. Next: #12 collectors + MQTT bridge.

## Product vision (the real endgame)

Simulated industrial machines stream telemetry over MQTT/OPC-UA → ML models
(NASA C-MAPSS dataset) predict Remaining Useful Life (RUL) → failing assets
auto-generate maintenance work orders → live dashboard.
Target stack: FastAPI + PostgreSQL/TimescaleDB · Next.js/TS frontend ·
scikit-learn → PyTorch LSTM/1D-CNN (MLflow + DVC) · Mosquitto MQTT + asyncua
OPC-UA (Kafka in Phase 5) · Docker, GitHub Actions, Prometheus/Grafana, Evidently.

## Verified repo state (2026-11-06)

- Monorepo, uv-managed. Real code: `apps/api` (FastAPI) +
  `services/simulator` (OPC-UA fleet simulator, merged via PR #43).
  Placeholder READMEs: `apps/web`, `services/ml`.
- Routers: `app/api/routes/` — auth.py, orgs.py, assets.py,
  maintenance_records.py, work_orders.py (assets + maint + work orders
  registered at `/orgs` prefix)
- Models: `app/models/` — User, Organization, OrganizationMember, Asset,
  WorkOrder, MaintenanceRecord (+ enums)
- Auth: JWT access 15 min + refresh 7 days, bcrypt registration
- Roles: **admin / viewer / agent** (NOT "member" — earlier notes were wrong)
- Tests: **50/50 passing** locally AND green in CI (re-verified 2026-11-06
  on merged main).
  Per-file breakdown: test_auth 11 · test_orgs 10 · test_assets 8 ·
  test_maintenance_records 9 · test_work_orders 10 · test_health 2.
  conftest self-heals `prognosiq_test` locally (fails if server down);
  in CI the workflow provisions `prognosiq_test` itself (docker exec psql)
  and conftest's self-heal path never runs there
- Infra: docker-compose, Postgres 127.0.0.1:5432, container `prognosiq-db-1`,
  Docker Desktop (Windows) must be running first
- Dev workflow: `.venv/bin/python` (no bare `python` on PATH) · tests:
  `cd apps/api && /home/dev/prognosiq/.venv/bin/python -m pytest -q` ·
  server: `uv run uvicorn app.main:app --reload` ·
  lint (every commit, Rule 8): `.venv/bin/ruff check --fix apps/api &&
  .venv/bin/ruff format apps/api` from repo root
- `services/simulator/` — REAL uv sub-project now (own pyproject.toml +
  uv.lock + .venv, Python 3.12, asyncua; NOT the root venv). Tests:
  `cd services/simulator && uv run pytest -q` → 19/19 green (2026-11-06),
  no DB/Docker needed (integration tests serve on 127.0.0.1:48410, NOT 4840).
  Modules: `simulator/{config,fleet,degradation,main}.py` · tests:
  test_{degradation,config,fleet,server}.py · demo `config.toml` (6 machines
  / 2 orgs) · `probe.py` dumps live fleet · boot: `uv run python -m
  simulator.main` · CLI tree dump:
  `uv run uals -l 4 opc.tcp://localhost:4841/prognosiq/simulator/`
  (4841 = containerized fleet's published port; a host-run server uses 4840)

## Git state

- 2026-11-06 (post-merge wrap): #11 DONE & MERGED — PR #43 squash →
  b65e891 on main; issue #11 CLOSED automatically. PR #44 (a60fe8d) folded
  the PR number into this file. Branch sweep: ALL stale local branches
  deleted (docs/adr-0002, docs/adr-0002-cleanup, docs/close-ticket-9,
  feat/api-skeleton, fix/session-import, feat/simulator-hello-fleet,
  docs/post-11-progress-number) — each verified with
  `git cherry main <branch>` (every line `-` = content already in main
  via squash) before deletion; only `main` remains. Post-merge gates on
  main: sim 19/19 · api 50/50 (re-run 2026-11-06).
- Squash-workflow lesson: `git branch -d` refuses squash-merged branches
  (ancestry is broken). Verify content with `git cherry main <branch>` —
  every line `-` = safe to `-D`. Immediately after a PR merge, `-d` may
  pass anyway via the upstream-ref check.
- Working tree clean, no pending work. Next work = new branch off updated main.
- Workflow from now on: branch → lint (Rule 8) → code → pytest → commit →
  PR ("Closes #N") → squash-merge (established pattern: #27, #33, #43).
  CLAUDE.md (repo root, created 2026-11-03) is auto-loaded every session
  and directs the AI to this file first.

## Next task: #12 — OPC-UA collectors + MQTT bridge (`services/collector/`)

- Depends on #11 ✅ DONE (simulator serves the fleet, containerized;
  `services/simulator/README.md` documents the address space and the
  identity-property contract).
- FIRST STEP (Rule 1): read `services/simulator/README.md` and
  `services/simulator/simulator/main.py` (the property contract the
  collector consumes) BEFORE writing any collector code; then decide the
  `services/collector/` module layout.
- ADR-0002 obligations: build the API telemetry ingestion endpoint (single
  write path) · collector buffers + retries on API downtime · JSON payload
  `"v": 1` · topic `prognosiq/orgs/{org}/assets/{asset}/telemetry` ·
  telemetry table created AS a hypertable · compose + CI postgres images
  → `timescale/timescaledb` (pg17).
- asyncua client using SUBSCRIPTIONS (not polling) · Mosquitto in compose ·
  reads OrgId/AssetId/AssetType/Health properties per machine (the #11
  contract) · reconnect resilience · tests against local OPC-UA + local
  MQTT · demo: mosquitto_sub shows live values for every simulated asset.

## Last task: ADR-0002 dual-protocol pipeline — ACCEPTED 2026-11-03 (PR #41)

- The four decisions: ingestion VIA API (single write path; ML-5 will reuse
  the same service-account pattern) · TimescaleDB enabled NOW (compose + CI
  images swap to `timescale/timescaledb` pg17; hypertable at table creation
  in #12) · JSON payload with version field `"v": 1` · numeric Kafka
  triggers (>1k msgs/sec sustained 10 min, OR 2nd consumer needing replay,
  OR 3rd service consuming the stream).
- Wire contract: topic `prognosiq/orgs/{org_id}/assets/{asset_id}/telemetry`
- Derived work now REQUIRED downstream: API telemetry ingestion endpoint,
  collector buffer-and-retry on API downtime, image swaps (compose + CI) —
  folded into Roadmap #11/#12 briefs.

## Last task: CI test job (#9) — DONE 2026-11-03 (PRs #38, #39)

- ci.yml existed since the skeleton but was SCHEMA-BROKEN — `test:` job at
  column 0 (top-level key) → every run failed in 0s since repo creation.
  Lesson: valid YAML ≠ valid workflow; 0s failure = file-level problem.
- Fixed schema (#38) → runs executed but failed on Postgres auth. Debugged
  with a temporary docker/psql step INSIDE the workflow; the service
  container's own logs showed: auth to `prognosiq_test` OK (db missing),
  auth to `prognosiq` (conftest's self-create admin path) rejected.
- Fix (#39): workflow provisions `prognosiq_test` itself via
  `docker exec psql` before pytest — conftest's self-heal never runs in CI.
  Job-level `DATABASE_URL` env removed (misleading, unused by tests).
- Badge added to root README. CI now green: 50 passed in ~1m9s.
  (Underlying scram anomaly on the admin-path connection left unidentified —
  path removed from CI, non-blocking.)

## Last task: work orders CRUD (#8) — merged via #36

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
- Simulator (verified 2026-11-06): `simulator/degradation.py` → SENSORS ·
  MachineProfile (frozen dataclass) · TYPE_PROFILES (5 keys mirroring
  AssetType: pump/motor/turbofan/compressor/conveyor) · ALLOWED_ASSET_TYPES ·
  MachineState · next_state · read_sensors · `simulator/config.py` →
  MachineConfig / SimulatorConfig / load_config(path=None) ·
  `simulator/fleet.py` → build_fleet(cfg, rng=None) · `simulator/main.py` →
  NAMESPACE_URI · run(cfg) · main() (argv[1] = config path, default
  config.toml). asyncua facts: node.add_property(idx, name, val) verified
  (node.py:913); QualifiedName attr is `.Name` NOT `.name` (uatypes.py:711);
  get_child paths are relative to the node called on (no leading "0:Objects"
  from nodes.objects)
- test_server.py (2026-11-06): ENDPOINT 127.0.0.1:48410 (deliberately ≠
  4840 — tests never fight a demo server or zombie) · make_cfg() builds
  SimulatorConfig in code (the DI path) · fixture teardown (cancel + await)
  runs even when the test body fails

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
9. LEARNING MODE (2026-11-03): @Proudly95's goal is to learn by doing.
   AI = instructor: give instructions + code + the "why", but the USER
   manually creates files / runs commands / commits / opens PRs.
   AI does hands-on work only when explicitly asked.

## Board (@Proudly95's PrognosIQ GitHub Project)

- Done: #1 skeleton, #2 docker compose, #3 models+Alembic, #4 registration,
  #5 JWT login, #6 orgs+RBAC, #7 assets CRUD + pagination (PR #33),
  #8 work orders CRUD (PR #36), #9 CI test job — green + badge (PRs #38/#39),
  #10 ADR-0001, #13 ADR-0002 (PR #41),  #11 SimulatorL OPC-UA (PR #43)
- Backlog: #12 collectors + MQTT bridge ← NEXT UP

## Roadmap (ticket briefs — added 2026-11-03, fact-checked)

Recommended order: #8 → #9 → #13 → #11 → #12 → ML-1…4 (parallelizable
anytime) → ML-5 → dashboard → monitoring. (ML-1/ML-2 need only the static
C-MAPSS files — can start in parallel with anything.)

### #8 — Work orders CRUD + pagination ✅ MERGED via #36 (suite 50/50)
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

### #9 — pytest setup + CI test job ✅ DONE 2026-11-03 (PRs #38/#39)
- ci.yml existed since the skeleton but was schema-broken (never ran);
  fixed, postgres:17 service container, test db provisioned by the workflow
  itself, badge live in root README. CI green: 50 passed (~1m9s).
- ⚠️ CORRECTION (now moot): alembic was never a missing dependency —
  it is in `pyproject.toml` deps + `uv.lock`.

### #13 — ADR-0002: dual-protocol integration ✅ ACCEPTED 2026-11-03 (PR #41)
- Same format as ADR-0001. Decisions to record: ingestion path (MQTT
  consumer → DB vs API endpoint) · TimescaleDB timing (hypertables for
  telemetry) · payload format (JSON now; protobuf/Avro later?) · what
  triggers the Phase-5 Kafka switch. Link from README when merged.

### #11 — SimulatorL OPC-UA server (`services/simulator/`) ✅ DONE 2026-11-06 (this PR, Closes #11)
- asyncua server; address space `/Fleet` → machine objects → sensor
  variables; machine types matching the AssetType enum
- Degradation engine: normal telemetry + C-MAPSS-style sensor drift toward
  failure (learnable signal for the ML models)
- Config-driven: machine count, failure modes, sample interval
- Dockerfile + compose entry; endpoint `opc.tcp://…:4840`
- Tests: server boots, tree browsable, values change over time; README
  documents the address-space design. Design the tree with #12/#13 in mind.

### #12 — OPC-UA collectors + MQTT bridge (`services/collector/`) — depends on #11
- ADR-0002 obligations: build the API telemetry ingestion endpoint (single
  write path) · collector buffers and retries on API downtime · JSON
  payload `"v": 1` · topic `prognosiq/orgs/{org}/assets/{asset}/telemetry` ·
  telemetry table created AS a hypertable · compose + CI postgres images
  switch to `timescale/timescaledb` (pg17)
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
- CI run failing in 0s = invalid workflow FILE (schema error, e.g. a job
  key at wrong indent), NOT a test failure. Debug deeper failures with a
  temporary docker/psql step inside the workflow and read the SERVICE
  container's own logs. (Learned fixing #9, 2026-11-03.)
- Simulator gotchas (2026-11-06): Errno 98 "address already in use" =
  old server still holds 4840 → `ss -tlnp | grep 4840` / `pkill -f
  simulator.main` · pre-commit stash-conflict: unstaged files + a hook
  auto-fix → it rolls back EVERYTHING; stage all then re-commit (Rule 8
  dance) · ruff reports ONLY syntax errors for a broken file — semantic
  checks (F401 etc.) surface after syntax is fixed · indentation is control
  flow: config.py validation nested one level deep ran per-key and made a
  VALID config raise "duplicate machine name" on machine #0; one test
  stayed green for the WRONG reason — green ≠ correct, check why ·
  typo'd dict keys ("Interval_s", m["names"]) are invisible to ruff — only
  tests catch them
- Async test lessons (2026-11-06): with background tasks the SETUP error
  (e.g. "server never came up") is almost never the cause — read the
  captured log for the task's own exception (KeyError: 'Turbofan' hid
  there) · `await` inside a bare `(… for …)` genexp makes an async
  generator that sorted()/list() reject (PEP 530) — use a list comp ·
  constructing SimulatorConfig in code skips load_config validation —
  closed via MachineConfig.__post_init__ asset_type check
- Docker/OPC-UA gotchas (2026-11-06): opcualds.exe (OPC-UA Local Discovery
  Server, Windows service) permanently owns host port 4840 → Docker
  Desktop can't forward 4840; simulator publishes 4841:4840 · container
  stdout is block-buffered — the print() banner is invisible until
  PYTHONUNBUFFERED=1 (set in the Dockerfile); missing banner ≠ dead
  server · WSL-side ports (host-run simulator on 4840) are a separate
  namespace, unaffected by the Windows LDS
