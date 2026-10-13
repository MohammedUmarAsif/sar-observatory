"""Scientific behavior checks, independent references and failure boundaries."""

from dataclasses import replace

import numpy as np
import pytest

from sar_observatory.config import C_M_S, Sensor
from sar_observatory.earth import block_change_interval, otsu_threshold
from sar_observatory.focusing import (
    backproject,
    direct_reference_pixel,
    image_axes,
    range_compress,
    reference_chirp,
)
from sar_observatory.metrics import assess, impulse_metrics, quality_gate
from sar_observatory.pipeline import run
from sar_observatory.simulator import axes, scene, simulate


@pytest.fixture(scope="module")
def focused():
    s = Sensor()
    raw, _ = simulate(s)
    compressed = range_compress(raw, s)
    x, y = image_axes(s)
    image = backproject(compressed, s, x, y)
    return s, raw, compressed, x, y, image


def test_units_and_delay():
    s = Sensor()
    eta, px, t = axes(s)
    assert np.diff(px)[0] == pytest.approx(s.velocity_m_s / s.prf_hz)
    assert np.diff(t)[0] == pytest.approx(1 / s.sample_rate_hz)
    assert t[s.range_samples // 2] == pytest.approx(2 * s.slant_m / C_M_S)
    assert eta.mean() == pytest.approx(0, abs=1e-16)
    assert s.expected_widths()["ground_m"] > s.expected_widths()["slant_m"]


def test_complex_matched_filter_matches_direct_convolution(focused):
    s, raw, compressed, *_ = focused
    pulse = reference_chirp(s)
    expected = np.convolve(raw[21], pulse.conj()[::-1], "same") / np.sum(abs(pulse) ** 2)
    np.testing.assert_allclose(compressed[21], expected, atol=1e-12)
    assert np.iscomplexobj(compressed)


def test_point_resolution_and_independent_reference(focused):
    s, raw, _, x, y, image = focused
    metrics = assess(image, x, y)
    assert metrics["localization_m"] < 0.1
    assert metrics["azimuth"]["width_m"] == pytest.approx(
        s.expected_widths()["azimuth_m"], rel=0.10
    )
    assert metrics["ground_range"]["width_m"] == pytest.approx(
        s.expected_widths()["ground_m"], rel=0.15
    )
    assert abs(direct_reference_pixel(raw, s)) == pytest.approx(1, abs=1e-5)
    assert abs(image).max() == pytest.approx(1, abs=0.10)
    # Off-target independent raw-domain prediction is much smaller.
    assert abs(direct_reference_pixel(raw, s, x_m=1)) < 0.1
    assert quality_gate(metrics, s.expected_widths())["passed"]


def test_sinc_metric_reference():
    x = np.linspace(-8, 8, 16001)
    m = impulse_metrics(x, np.sinc(x))
    assert m["width_m"] == pytest.approx(0.88589, abs=1e-4)
    assert m["pslr_db"] == pytest.approx(-13.261, abs=0.005)
    # Finite +/-8-null window intentionally differs from infinite sinc energy.
    assert -11 < m["islr_db"] < -9


def test_velocity_mismatch_blurs(focused):
    s, _, rc, x, y, image = focused
    bad = assess(backproject(rc, s, x, y, 0.03), x, y)
    good = assess(image, x, y)
    assert bad["azimuth"]["width_m"] > 1.4 * good["azimuth"]["width_m"]
    assert not quality_gate(bad, s.expected_widths())["passed"]


def test_doppler_shift_evades_width_gate():
    s = Sensor()
    raw, _ = simulate(s, doppler_hz=4)
    x, y = image_axes(s)
    metrics = assess(backproject(range_compress(raw, s), s, x, y), x, y)
    expected_shift = 4 * s.wavelength_m * s.slant_m / (2 * s.velocity_m_s)
    assert abs(metrics["peak_xy_m"][0]) == pytest.approx(expected_shift, abs=0.07)
    gate = quality_gate(metrics, s.expected_widths())
    assert gate["checks"]["width"]
    assert not gate["checks"]["localization"]


def test_bandwidth_and_aperture_scaling():
    s = Sensor()
    for modified, component in [
        (replace(s, bandwidth_hz=20e6), "ground_range"),
        (replace(s, pulses=256), "azimuth"),
    ]:
        raw, _ = simulate(modified)
        x, y = image_axes(modified)
        m = assess(backproject(range_compress(raw, modified), modified, x, y), x, y)
        expected = modified.expected_widths()[
            "ground_m" if component == "ground_range" else "azimuth_m"
        ]
        assert m[component]["width_m"] == pytest.approx(expected, rel=0.15)


def test_noise_power_and_reproducibility():
    s = Sensor()
    clean, _ = simulate(s, snr_db=200)
    noisy, definition = simulate(s, snr_db=-5)
    np.testing.assert_array_equal(noisy, simulate(s, snr_db=-5)[0])
    assert np.mean(abs(noisy - clean) ** 2) == pytest.approx(
        definition["injected_noise_power"], rel=0.01
    )
    assert not np.array_equal(noisy, simulate(replace(s, seed=18), snr_db=-5)[0])


@pytest.mark.parametrize(
    "raw", [np.ones((512, 512)), np.full((512, 512), np.nan + 1j), np.ones((2, 2), complex)]
)
def test_corrupted_input_rejected(raw):
    with pytest.raises(ValueError):
        run(Sensor(), raw_input=raw)


@pytest.mark.parametrize(
    "settings",
    [
        {"sample_rate_hz": 10e6},
        {"prf_hz": 50},
        {"velocity_m_s": -1},
        {"pulses": 50000},
        {"pulse_s": float("nan")},
    ],
)
def test_sampling_configuration_rejected(settings):
    with pytest.raises(ValueError):
        Sensor(**settings)


def test_extended_scene_and_invalid_targets():
    s = Sensor()
    assert len(scene(s, extended=True)) > 3
    with pytest.raises(ValueError, match="supported"):
        simulate(s, [(100, 1000, 1)])
    with pytest.raises(ValueError, match="finite"):
        simulate(s, snr_db=float("nan"))


def test_invalid_metric_windows():
    with pytest.raises(ValueError):
        impulse_metrics(np.arange(20), np.zeros(20))
    with pytest.raises(ValueError):
        impulse_metrics(np.arange(20), np.ones(20))


def test_otsu_bimodal_and_block_dependence():
    values = np.r_[np.linspace(-25, -20, 100), np.linspace(-10, -5, 100)]
    assert -20 <= otsu_threshold(values) <= -10
    with pytest.raises(ValueError):
        otsu_threshold(np.ones(100) * -10)
    valid = np.ones((256, 256), bool)
    before, after = np.zeros_like(valid), np.ones_like(valid)
    result = block_change_interval(before, after, valid)
    assert result["blocks"] == 4
    assert result["change_fraction_interval_95"] == [1.0, 1.0]
