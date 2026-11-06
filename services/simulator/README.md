# SimulatorL — simulated industrial fleet speaking OPC-UA

Simulated machines stream live telemetry over OPC-UA for the PrognosIQ
pipeline: collector (#12) → API ingestion → TimescaleDB → ML (RUL).
This service stands in for a real factory floor during development.

## Address space

`Objects → 2:Fleet → one object per machine → variables + properties`

Each machine object carries:

- sensor variables: `rpm`, `temperature_c`, `vibration_mm_s` (rewritten every tick)
- identity properties: `OrgId`, `AssetId`, `AssetType`, `Health`

The identity properties are the contract with the #12 collector: it reads
`OrgId` + `AssetId` to build MQTT topics
`prognosiq/orgs/{org}/assets/{asset}/telemetry` (ADR-0002).

`AssetType` values mirror the API's `AssetType` enum (`apps/api`
`app/models/enums.py`): pump · motor · turbofan · compressor · conveyor.

## Degradation model (the ML signal)

Health starts at 1.0 and decays to 0.0. Each reading is
`baseline + wear_gain × (1 − health) + noise`, and every asset type has
its own signature:

| type       | signature            |
|------------|----------------------|
| pump       | vibration-led        |
| motor      | temperature-led      |
| turbofan   | all three rise       |
| compressor | rpm-led              |
| conveyor   | vibration-led, slow  |

Values are stylized, not physically calibrated. Profile definitions live
in code (`simulator/degradation.py`); *which machines run* lives in
`config.toml` — code = behavior, config = fleet.

## Configuration

`config.toml` sits next to the code and is mountable over at runtime:

```toml
[simulator]
endpoint = "opc.tcp://0.0.0.0:4840/prognosiq/simulator/"
interval_s = 1.0

[[machine]]
name = "Pump-01"
org_id = "org-1"
asset_id = "asset-101"
asset_type = "pump"
```

Validated on load: unique names/asset ids, known asset types, interval > 0.

## Run

Local:

```bash
cd services/simulator
uv run python -m simulator.main   # serve the fleet from config.toml
uv run python probe.py            # dump the live tree as a client
uv run pytest -q                  # 19 tests (unit + in-process OPC-UA on 48410)
```

Docker:

```bash
docker compose build simulator
docker compose up -d simulator    # publishes host port 4841
docker compose logs -f simulator
```

**Why host port 4841?** Docker Desktop's port forwarder binds on the
Windows side, where an OPC-UA Local Discovery Server (`opcualds.exe`)
permanently owns 4840. The container maps 4841 → 4840. A host-run
simulator can still use 4840 inside WSL's separate network namespace.

Browse the tree from a terminal:

```bash
uv run uals -l 4 opc.tcp://localhost:4841/prognosiq/simulator/
```

## Security

None — the endpoint is open and unencrypted by design. Dev tooling only;
never expose beyond localhost.
