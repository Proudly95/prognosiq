ADR-0001: Founding scope and architecture
Date: 2026-10-08 Status: Accepted

Context
PrognosIQ targets predictive maintenance for industrial fleets. The productloop: telemetry in → RUL prediction → work orders out. This requires a webplatform (auth, assets, work orders), a streaming pipeline, and anoffline-train / online-serve ML split.

Decision
Monorepo: apps/ (api, web) + services/ (ml, simulator). SynchronousSQLAlchemy 2.0 with psycopg3 — CRUD-dominant workload, readability first;FastAPI runs sync endpoints in a threadpool. Time-series storage onTimescaleDB, a Postgres extension, so app data and telemetry share oneengine. Telemetry ingestion is dual-protocol from the start: MQTT forsensor-grade devices, OPC-UA for PLC-grade machines, bridged into onepipeline.

Consequences
Positive: one repo, one CI pipeline, one database engine to operate; synccode is simple to read and debug; dual-protocol ingestion matches realfactory environments.Negative: a later move to async touches every endpoint; TimescaleDB couplestelemetry storage to Postgres; two protocols mean two ingestion paths tomaintain.
