from pathlib import Path

import pytest
from simulator.config import load_config

VALID = """
[simulator]
endpoint = "opc.tcp://0.0.0.0:4840/prognosiq/simulator/"
interval_s = 0.5

[[machine]]
name = "Pump-01"
org_id = "org-1"
asset_id = "asset-101"
asset_type = "pump"

[[machine]]
name = "Motor-01"
org_id = "org-1"
asset_id = "asset-102"
asset_type = "motor"
"""


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(text)
    return path


def test_load_valid_config(tmp_path):
    cfg = load_config(write_config(tmp_path, VALID))
    assert cfg.interval_s == 0.5
    assert [m.name for m in cfg.machines] == ["Pump-01", "Motor-01"]
    assert cfg.machines[0].asset_type == "pump"


def test_unknown_asset_type_rejected(tmp_path):
    bad = VALID.replace('asset_type = "motor"', 'asset_type = "lathe"')
    with pytest.raises(ValueError, match="unknown asset_type"):
        load_config(write_config(tmp_path, bad))


def test_duplicate_names_rejected(tmp_path):
    dup = VALID.replace('name = "Motor-01"', 'name = "Pump-01"')
    with pytest.raises(ValueError, match="duplicate machine name"):
        load_config(write_config(tmp_path, dup))


def test_non_positive_interval_rejected(tmp_path):
    bad = VALID.replace("interval_s = 0.5", "interval_s = 0")
    with pytest.raises(ValueError, match="interval_s"):
        load_config(write_config(tmp_path, bad))


def test_missing_key_rejected(tmp_path):
    bad = VALID.replace('asset_id = "asset-102"\n', "")
    with pytest.raises(ValueError, match="missing 'asset_id'"):
        load_config(write_config(tmp_path, bad))
