ADR-0002: Dual-protocol telemetry pipeline
Date: 2026-11-03 Status: Accepted

Context
ADR-0001 fixed dual-protocol ingestion (MQTT for sensor-grade devices,
OPC-UA for PLC-grade machines) and chose TimescaleDB as the engine. Four
implementation decisions remained: how telemetry reaches the database,
when to adopt TimescaleDB hypertables, the wire payload format, and what
would ever justify Kafka. Scale is modest: one developer, simulated fleet
of dozens of machines, well under 1k messages/sec, readability-first.

Decision
Ingestion via API: collectors subscribe (OPC-UA) or consume (MQTT) and
POST batches to a single authenticated ingestion endpoint. The API is the
only writer of telemetry rows — one validation path, one schema owner,
and the same service-account pattern the ML-5 work-order hook will reuse.
TimescaleDB is enabled NOW: docker images in compose and CI switch from
postgres:17 to timescale/timescaledb (pg17 tag), and #12 creates the
telemetry table as a hypertable from row one — honoring ADR-0001 and
avoiding a guaranteed later migration. Payload is JSON with a version
field, human-readable for debugging, cheap to evolve; binary formats
(Avro/protobuf) only if a Kafka trigger fires. Topic scheme:
prognosiq/orgs/{org_id}/assets/{asset_id}/telemetry
Kafka triggers, recorded numerically: sustained ingest above 1,000
msgs/sec for 10 minutes, OR a second independent consumer requiring
replay, OR a third service consuming the same stream. Until one fires,
Mosquitto plus the API endpoint is the entire pipeline.

Example payload (the #12 contract):
{
  "v": 1,
  "asset_id": 42,
  "ts": "2026-11-03T12:00:00.123Z",
  "metrics": { "rpm": 1480.2, "temperature_c": 73.4, "vibration_mm_s": 2.1 }
}

Consequences
Positive: single write path keeps validation and schema ownership in the
API; hypertable from row one, no migration debt; JSON is debuggable by
anyone with mosquitto_sub; versioned payload makes wire-format changes
non-breaking; numeric Kafka triggers turn a future debate into a check.
Negative: API downtime pauses telemetry, so the collector must
buffer-and-retry; the TimescaleDB image must be tracked separately from
vanilla postgres in BOTH compose and CI; JSON is larger and slower to
parse than binary formats at high volume; the 1k msgs/sec trigger is an
estimate, not a measured limit.
