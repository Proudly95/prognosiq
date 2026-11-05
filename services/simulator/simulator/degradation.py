"""C-MAPSS-style degradation: machines drift toward failure.

Health starts at 1.0 (healthy) and decays to 0.0 (failed). Degraded
machines show classic turbofan signatures: rpm creeps up, temperature
and vibration rise. The drift is the learnable signal for the RUL models.
"""

import random
from dataclasses import dataclass


@dataclass
class MachineState:
    name: str
    health: float = 1.0  # 1.0 healthy -> 0.0 failed
    degrade_rate: float = 0.01  # health lost per tick
    baseline_rpm: float = 1500.0


def next_state(state: MachineState) -> MachineState:
    """Advance one simulation tick: decay health, floor at zero."""
    state.health = max(0.0, state.health - state.degrade_rate)
    return state


def read_sensors(state: MachineState, rng: random.Random | None = None) -> dict[str, float]:
    """Sensor readings for the current state: baseline + wear signature + noise."""
    rng = rng or random.Random()
    wear = 1.0 - state.health  # 0.0 healthy -> 1.0 failed
    return {
        "rpm": state.baseline_rpm * (1 + 0.05 * wear) + rng.uniform(-10, 10),
        "temperature_c": 65.0 + 25.0 * wear + rng.uniform(-1.5, 1.5),
        "vibration_mm_s": 1.5 + 3.5 * wear + rng.uniform(-0.2, 0.2),
    }
