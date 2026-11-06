"""Load and validate simulator config from TOML."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

from simulator.degradation import ALLOWED_ASSET_TYPES


@dataclass(frozen=True)
class MachineConfig:
    name: str
    org_id: str
    asset_id: str
    asset_type: str


@dataclass(frozen=True)
class SimulatorConfig:
    endpoint: str
    interval_s: float
    machines: list[MachineConfig]


def load_config(path: Path | None = None) -> SimulatorConfig:
    """Parse config.toml (or the given path); raise ValueError on bad config."""
    path = path or Path("config.toml")
    with path.open("rb") as f:
        raw = tomllib.load(f)

    sim = raw.get("simulator", {})
    endpoint = sim.get("endpoint")
    if not endpoint:
        raise ValueError("[simulator] endpoint is required")
    interval_s = float(sim.get("interval_s", 1.0))
    if interval_s <= 0:
        raise ValueError("[simulator] interval_s must be > 0")

    machines: list[MachineConfig] = []
    seen_names: set[str] = set()
    seen_ids: set[str] = set()
    for i, m in enumerate(raw.get("machine", [])):
        for key in ("name", "org_id", "asset_id", "asset_type"):
            if not m.get(key):
                raise ValueError(f"machine #{i}: missing '{key}'")
        if m["asset_type"] not in ALLOWED_ASSET_TYPES:
            known = ", ".join(sorted(ALLOWED_ASSET_TYPES))
            raise ValueError(
                f"machine {m['name']}: unknown asset_type '{m['asset_type']}' (known: {known})"
            )
        if m["name"] in seen_names:
            raise ValueError(f"duplicate machine name '{m['name']}'")
        if m["asset_id"] in seen_ids:
            raise ValueError(f"duplicate asset_id '{m['asset_id']}'")
        seen_names.add(m["name"])
        seen_ids.add(m["asset_id"])
        machines.append(
            MachineConfig(
                name=m["name"],
                org_id=m["org_id"],
                asset_id=m["asset_id"],
                asset_type=m["asset_type"],
            )
        )
    if not machines:
        raise ValueError("at least one [[machine]] entry is required")

    return SimulatorConfig(endpoint=endpoint, interval_s=interval_s, machines=machines)
