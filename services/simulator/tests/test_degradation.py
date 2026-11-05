import random

from simulator.degradation import MachineState, next_state, read_sensors


def test_health_decays_toward_zero():
    state = MachineState(name="M-01")
    for _ in range(50):
        next_state(state)
    assert state.health < 1.0


def test_health_never_below_zero():
    state = MachineState(name="M-01", health=0.01)
    for _ in range(10):
        next_state(state)
    assert state.health == 0.0


def test_degraded_machine_runs_hotter():
    healthy = read_sensors(MachineState(name="M-01", health=1.0), rng=random.Random(1))
    worn = read_sensors(MachineState(name="M-01", health=0.0), rng=random.Random(1))
    assert worn["temperature_c"] > healthy["temperature_c"]
    assert worn["vibration_mm_s"] > healthy["vibration_mm_s"]
