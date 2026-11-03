# PrognosIQ API

FastAPI backend for PrognosIQ: JWT auth, organizations with role-based access
(admin / viewer / agent), assets, maintenance records, and work orders.

Routes: `/auth`, `/health` — plus `/orgs/{org_id}/assets` and
`/orgs/{org_id}/assets/{asset_id}/maintenance-records` (org-scoped RBAC).

## Setup

Requires Docker Desktop running first (Postgres at 127.0.0.1:5432, container
`prognosiq-db-1`).

```bash
docker compose up -d                # repo root
cd apps/api
~/prognosiq/.venv/bin/alembic upgrade head   # apply migrations
uv run uvicorn app.main:app --reload         # dev server on :8000
```

## Tests

```bash
cd apps/api && ~/prognosiq/.venv/bin/python -m pytest -q
```

Tests run against a self-healing `prognosiq_test` database (created
automatically; the Postgres server must be up). Dev DB schema changes go
through Alembic only.
