import random

from simulator.config import MachineConfig, SimulatorConfig
from simulator.degradation import TYPE_PROFILES
from simulator.fleet import build_fleet


def make_cfg() -> SimulatorConfig:
    return SimulatorConfig(
        endpoint="opc.tcp://localhost:4840/x",
        interval_s=1.0,
        machines=[
            MachineConfig(
                name="Pump-01",
                org_id="org-1",
                asset_id="asset-101",
                asset_type="pump",
            ),
            MachineConfig(
                name="Turbofan-01",
                org_id="org-1",
                asset_id="asset-103",
                asset_type="turbofan",
            ),
            MachineConfig(
                name="Conveyor-01",
                org_id="org-2",
                asset_id="asset-202",
                asset_type="conveyor",
            ),
        ],
    )


def test_builds_one_state_per_entry_with_identity():
    fleet = build_fleet(make_cfg(), rng=random.Random(42))
    assert [m.name for m in fleet] == ["Pump-01", "Turbofan-01", "Conveyor-01"]
    assert fleet[0].profile is TYPE_PROFILES["pump"]
    assert fleet[2].org_id == "org-2"
    assert fleet[1].asset_id == "asset-103"


def test_degrade_rates_within_profile_range_and_deterministic():
    a = build_fleet(make_cfg(), rng=random.Random(42))
    b = build_fleet(make_cfg(), rng=random.Random(42))
    assert [m.degrade_rate for m in a] == [m.degrade_rate for m in b]
    for m in a:
        lo, hi = m.profile.degrade_rate_range
        assert lo <= m.degrade_rate <= hi


def test_health_starts_at_one():
    fleet = build_fleet(make_cfg())
    assert all(m.health == 1.0 for m in fleet)
