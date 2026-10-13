"""Integrity boundaries and credential-free end-to-end publication checks."""

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from sar_observatory import pipeline
from sar_observatory.config import Sensor
from sar_observatory.earth import analyze, load_pair
from sar_observatory.experiments import generate


def test_verified_cache_and_tampering(tmp_path, monkeypatch):
    original_root = pipeline.ROOT
    shutil.copy(original_root / "uv.lock", tmp_path / "uv.lock")
    monkeypatch.setattr(pipeline, "ROOT", tmp_path)
    sensor = Sensor(pulses=256)
    first, arrays = pipeline.run(sensor)
    reused, again = pipeline.run(sensor)
    assert reused == first
    np.testing.assert_array_equal(arrays["image"], again["image"])
    cached = tmp_path / "artifacts" / "cache" / first["key"] / "stages.npz"
    cached.write_bytes(b"deliberately corrupted cache")
    restored, result = pipeline.run(sensor)
    assert restored["image_sha256"] == first["image_sha256"]
    np.testing.assert_array_equal(result["image"], arrays["image"])


def test_real_crops_and_area_accounting():
    result, db, valid, masks = analyze()
    assert valid.mean() > 0.9
    assert (
        result["acquisitions"][0]["properties"]["sat:relative_orbit"]
        == result["acquisitions"][1]["properties"]["sat:relative_orbit"]
    )
    assert (
        result["acquisitions"][0]["properties"]["platform"]
        == result["acquisitions"][1]["properties"]["platform"]
    )
    expected_count = np.count_nonzero((db[0] < -17) & valid)
    assert result["methods"]["fixed"]["candidate_area_km2"][0] == pytest.approx(
        expected_count * 100 / 1e6
    )
    assert np.all(~masks["fixed"][0][~valid])
    # Mask nesting must hold for a fixed dB threshold: looser thresholds never reduce area.
    fractions = [result["threshold_sensitivity"][str(t)][0] for t in (-19, -18, -17, -16, -15)]
    assert all(a <= b for a, b in zip(fractions, fractions[1:], strict=False))


def test_full_artifact_generation():
    generate(cache=True)
    root = Path(__file__).resolve().parents[1]
    output = json.loads((root / "results" / "synthetic.json").read_text(encoding="utf-8"))
    assert output["gate_ablation"] == {
        "width_only_accepts_doppler": True,
        "full_gate_accepts_doppler": False,
    }
    assert output["cases"][0]["manifest"]["gate"]["passed"]
    assert output["corrupted_input"]["outcome"] == "rejected before processing"
    inventory = json.loads((root / "results" / "inventory.json").read_text(encoding="utf-8"))
    for relative, expected in inventory["files"].items():
        assert pipeline.checksum(root / relative) == expected
    assert (root / "docs" / "report.md").is_file()


def test_grid_mismatch_rejected(tmp_path, monkeypatch):
    import rasterio
    from rasterio.transform import Affine

    from sar_observatory import earth

    shutil.copytree(pipeline.ROOT / "data", tmp_path / "data")
    with rasterio.open(tmp_path / "data" / "after.tif", "r+") as changed:
        changed.transform = changed.transform @ Affine.translation(1, 0)
    monkeypatch.setattr(earth, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="identical CRS"):
        load_pair()
