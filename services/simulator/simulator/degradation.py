"""C-MAPSS-style degradation: machines drift toward failure.

Health starts at 1.0 (healthy) and decays to 0.0 (failed). Each asset
type has its own wear signature (which sensors move, and how fast the
machine degrades). The drift is the learnable signal for the RUL models.
"""

import random
from dataclasses import dataclass

SENSORS = ("rpm", "temperature_c", "vibration_mm_s")


@dataclass(frozen=True)
class MachineProfile:
    """How one asset type degrades: baselines, wear gains, noise, speed."""

    asset_type: str
    baseline: dict[str, float]  # healthy reading per sensor
    wear_gain: dict[str, float]  # amount added at full wear
    noise: dict[str, float]  # uniform +- jitter per reading
    degrade_rate_range: tuple[float, float]  # health loss per tick, min/max


TYPE_PROFILES: dict[str, MachineProfile] = {
    # vibration-led: impeller/cavitation wear
    "pump": MachineProfile(
        asset_type="pump",
        baseline={"rpm": 1450.0, "temperature_c": 60.0, "vibration_mm_s": 1.2},
        wear_gain={"rpm": 45.0, "temperature_c": 8.0, "vibration_mm_s": 4.5},
        noise={"rpm": 8.0, "temperature_c": 1.0, "vibration_mm_s": 0.15},
        degrade_rate_range=(0.004, 0.008),
    ),
    # temperature-led: winding/insulation wear
    "motor": MachineProfile(
        asset_type="motor",
        baseline={"rpm": 1750.0, "temperature_c": 70.0, "vibration_mm_s": 2.5},
        wear_gain={"rpm": 30.0, "temperature_c": 40.0, "vibration_mm_s": 0.6},
        noise={"rpm": 10.0, "temperature_c": 1.5, "vibration_mm_s": 0.1},
        degrade_rate_range=(0.003, 0.006),
    ),
    # full C-MAPSS triple: all three sensors rise hard
    "turbofan": MachineProfile(
        asset_type="turbofan",
        baseline={"rpm": 5000.0, "temperature_c": 450.0, "vibration_mm_s": 2.0},
        wear_gain={"rpm": 750.0, "temperature_c": 100.0, "vibration_mm_s": 1.0},
        noise={"rpm": 40.0, "temperature_c": 3.0, "vibration_mm_s": 0.2},
        degrade_rate_range=(0.002, 0.004),
    ),
    # rpm-led: surge/valve wear
    "compressor": MachineProfile(
        asset_type="compressor",
        baseline={"rpm": 3600.0, "temperature_c": 85.0, "vibration_mm_s": 4.0},
        wear_gain={"rpm": 650.0, "temperature_c": 6.0, "vibration_mm_s": 0.4},
        noise={"rpm": 25.0, "temperature_c": 2.0, "vibration_mm_s": 0.2},
        degrade_rate_range=(0.004, 0.009),
    ),
    # vibration-led, slow: bearing wear on a slow drum
    "conveyor": MachineProfile(
        asset_type="conveyor",
        baseline={"rpm": 90.0, "temperature_c": 45.0, "vibration_mm_s": 0.8},
        wear_gain={"rpm": 2.7, "temperature_c": 4.0, "vibration_mm_s": 2.0},
        noise={"rpm": 1.5, "temperature_c": 0.5, "vibration_mm_s": 0.05},
        degrade_rate_range=(0.001, 0.003),
    ),
}

ALLOWED_ASSET_TYPES: frozenset[str] = frozenset(TYPE_PROFILES)


@dataclass
class MachineState:
    name: str
    profile: MachineProfile
    org_id: str = "org-1"
    asset_id: str = ""
    health: float = 1.0  # 1.0 healthy -> 0.0 failed
    degrade_rate: float | None = None  # health lost per tick


def next_state(state: MachineState) -> MachineState:
    """Advance one simulation tick: decay health, floor at zero."""
    if state.degrade_rate is None:
        state.degrade_rate = random.uniform(*state.profile.degrade_rate_range)
    state.health = max(0.0, state.health - state.degrade_rate)
    return state


def read_sensors(state: MachineState, rng: random.Random | None = None) -> dict[str, float]:
    """Sensor readings for the current state: baseline + wear signature + noise."""
    rng = rng or random.Random()
    wear = 1.0 - state.health  # 0.0 healthy -> 1.0 failed
    return {
        s: state.profile.baseline[s]
        + state.profile.wear_gain[s] * wear
        + rng.uniform(-state.profile.noise[s], state.profile.noise[s])
        for s in SENSORS
    }
