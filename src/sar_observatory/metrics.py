"""Power-based 1D impulse metrics, with explicit finite-window conventions."""

import numpy as np
from scipy.signal import find_peaks


def impulse_metrics(axis_m, amplitude):
    """Half-power width, first-minimum PSLR/ISLR; no oversampling claim.

    Crossings use linear power interpolation. Sidelobes are defined outside the
    closest local minima around the peak, integrated over the supplied profile.
    Noisy minima can bias these metrics: this is recorded in the limitations.
    """
    x, a = np.asarray(axis_m), np.asarray(amplitude)
    if x.ndim != 1 or a.shape != x.shape or len(x) < 9 or not np.all(np.diff(x) > 0):
        raise ValueError("profile requires matching 1D samples and increasing metre coordinates")
    if not np.isfinite(a).all() or not np.isfinite(x).all():
        raise ValueError("profile must be finite")
    p = np.abs(a) ** 2
    k = int(np.argmax(p))
    if p[k] <= 0:
        raise ValueError("zero impulse has no width or sidelobe metrics")
    p = p / p[k]
    left_candidates = np.flatnonzero(p[:k] < 0.5)
    right_candidates = np.flatnonzero(p[k + 1 :] < 0.5) + k + 1
    if not len(left_candidates) or not len(right_candidates):
        raise ValueError("half-power response truncated by measurement window")
    left_index, r = int(left_candidates[-1]), int(right_candidates[0])
    left = x[left_index] + (0.5 - p[left_index]) / (p[left_index + 1] - p[left_index]) * (
        x[left_index + 1] - x[left_index]
    )
    right = x[r - 1] + (0.5 - p[r - 1]) / (p[r] - p[r - 1]) * (x[r] - x[r - 1])
    minima = find_peaks(-p)[0]
    lo, hi = minima[minima < k], minima[minima > k]
    if not len(lo) or not len(hi):
        raise ValueError("no first minima in profile; expand window or flag defocus")
    lo, hi = int(lo[-1]), int(hi[0])
    side = np.ones(len(x), dtype=bool)
    side[lo : hi + 1] = False
    # Profiles have constant spacing; discrete integrated energy with same dx.
    if not np.allclose(np.diff(x), np.diff(x)[0]):
        raise ValueError("sidelobe energy requires uniform spacing")
    return {
        "width_m": float(right - left),
        "peak_m": float(x[k]),
        "pslr_db": float(10 * np.log10(max(float(p[side].max()), 1e-30))),
        "islr_db": float(10 * np.log10(max(float(p[side].sum() / p[~side].sum()), 1e-30))),
        "mainlobe_bounds_m": [float(x[lo]), float(x[hi])],
        "window_m": [float(x[0]), float(x[-1])],
        "width_quantization_bound_m": float(2 * np.diff(x)[0]),
    }


def assess(image, x_m, y_m, expected_xy=(0.0, 1000.0)):
    power = np.abs(image) ** 2
    iy, ix = np.unravel_index(np.argmax(power), power.shape)
    az = impulse_metrics(x_m, image[iy, :])
    ground = impulse_metrics(y_m, image[:, ix])
    error = float(np.hypot(x_m[ix] - expected_xy[0], y_m[iy] - expected_xy[1]))
    return {
        "azimuth": az,
        "ground_range": ground,
        "localization_m": error,
        "peak_power": float(power[iy, ix]),
        "peak_xy_m": [float(x_m[ix]), float(y_m[iy])],
    }


def quality_gate(metrics, expected):
    """Educational thresholds selected a priori, not a vendor acceptance spec."""
    tests = {
        "width": metrics["azimuth"]["width_m"] <= 1.25 * expected["azimuth_m"],
        "range_width": metrics["ground_range"]["width_m"] <= 1.25 * expected["ground_m"],
        "localization": metrics["localization_m"] <= 0.35,
    }
    return {
        "passed": all(tests.values()),
        "checks": tests,
        "limits": {
            "azimuth_width_m": 1.25 * expected["azimuth_m"],
            "ground_width_m": 1.25 * expected["ground_m"],
            "localization_m": 0.35,
        },
    }
