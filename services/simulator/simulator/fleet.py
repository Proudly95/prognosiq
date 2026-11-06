import random

from simulator.config import SimulatorConfig
from simulator.degradation import TYPE_PROFILES, MachineState


def build_fleet(cfg: SimulatorConfig, rng: random.Random | None = None) -> list[MachineState]:
    """One MachineState per config entry; degrade rates drawn per type."""
    rng = rng or random.Random()
    states = []
    for m in cfg.machines:
        profile = TYPE_PROFILES[m.asset_type]
        states.append(
            MachineState(
                name=m.name,
                profile=profile,
                org_id=m.org_id,
                asset_id=m.asset_id,
                degrade_rate=rng.uniform(*profile.degrade_rate_range),
            )
        )
    return states
