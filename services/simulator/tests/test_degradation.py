import random

import pytest
from simulator.degradation import (
    SENSORS,
    TYPE_PROFILES,
    MachineState,
    next_state,
    read_sensors,
)


def make_state(**overrides) -> MachineState:
    overrides.setdefault("profile", TYPE_PROFILES["pump"])
    overrides.setdefault("degrade_rate", 0.01)
    return MachineState(name="M-01", **overrides)


def test_health_decays_toward_zero():
    state = make_state()
    for _ in range(50):
        next_state(state)
    assert state.health < 1.0


def test_health_never_below_zero():
    state = make_state(health=0.01)
    for _ in range(10):
        next_state(state)
    assert state.health == 0.0


def test_profile_cover_all_five_types_with_sensor_keysets():
    assert set(TYPE_PROFILES) == {"pump", "motor", "turbofan", "compressor", "conveyor"}
    for profile in TYPE_PROFILES.values():
        for table in (profile.baseline, profile.wear_gain, profile.noise):
            assert set(table) == set(SENSORS)


def test_wear_gain_exact_when_noise_cancels():
    # Same seeded rng for both calls: identical noise draws, so the
    # healthy->worn difference per sensor is exactly the wear gain.
    healthy_state = make_state(health=1.0)
    worn_state = make_state(health=0.0)
    healthy = read_sensors(healthy_state, rng=random.Random(7))
    worn = read_sensors(worn_state, rng=random.Random(7))
    for s in SENSORS:
        assert worn[s] - healthy[s] == pytest.approx(worn_state.profile.wear_gain[s])


def test_pump_is_vibration_led():
    p = TYPE_PROFILES["pump"]
    vib = p.wear_gain["vibration_mm_s"] / p.baseline["vibration_mm_s"]
    temp = p.wear_gain["temperature_c"] / p.baseline["temperature_c"]
    rpm = p.wear_gain["rpm"] / p.baseline["rpm"]
    assert vib > temp > rpm


def test_motor_is_temperature_led():
    p = TYPE_PROFILES["motor"]
    temp = p.wear_gain["temperature_c"] / p.baseline["temperature_c"]
    vib = p.wear_gain["vibration_mm_s"] / p.baseline["vibration_mm_s"]
    rpm = p.wear_gain["rpm"] / p.baseline["rpm"]
    assert temp > vib > rpm


def test_turbofan_shows_full_triple():
    p = TYPE_PROFILES["turbofan"]
    for s in SENSORS:
        assert p.wear_gain[s] / p.baseline[s] > 0.10


def test_degraded_machine_runs_hotter_and_shakes():
    healthy = read_sensors(make_state(health=1.0), rng=random.Random(1))
    worn = read_sensors(make_state(health=0.0), rng=random.Random(1))
    assert worn["temperature_c"] > healthy["temperature_c"]
    assert worn["vibration_mm_s"] > healthy["vibration_mm_s"]
