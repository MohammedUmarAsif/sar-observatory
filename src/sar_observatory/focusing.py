"""Linear range compression followed by direct geometric backprojection."""

import numpy as np
from scipy.signal import fftconvolve

from .config import C_M_S, Sensor
from .simulator import axes, chirp


def validate_raw(raw, sensor: Sensor):
    if raw.shape != (sensor.pulses, sensor.range_samples):
        raise ValueError(
            f"echo shape {raw.shape}; expected {(sensor.pulses, sensor.range_samples)}"
        )
    if not np.iscomplexobj(raw):
        raise ValueError("complex I/Q required; detected intensity cannot be focused")
    if not np.isfinite(raw).all():
        raise ValueError("echo contains NaN/Inf; stop before range compression")


def reference_chirp(sensor: Sensor):
    # Odd length preserves center sample alignment in 'same' linear convolution.
    half = int(np.ceil(sensor.pulse_s * sensor.sample_rate_hz / 2))
    return chirp(np.arange(-half, half + 1) / sensor.sample_rate_hz, sensor)


def range_compress(raw, sensor: Sensor):
    validate_raw(raw, sensor)
    pulse = reference_chirp(sensor)
    matched = pulse.conj()[::-1]
    return fftconvolve(raw, matched[None, :], mode="same", axes=1) / np.sum(np.abs(pulse) ** 2)


def image_axes(sensor: Sensor):
    return np.linspace(-8, 8, 321), sensor.center_ground_m + np.linspace(-30, 30, 121)


def backproject(compressed, sensor: Sensor, x_m, y_m, velocity_error=0.0):
    """Integrate complex compressed samples with carrier phase compensation.

    Output (ground-range y, along-track x). Linear interpolation of I/Q at exact
    delay. Pulses are averaged, with rectangular aperture weighting. Error is
    fractional assumed velocity; acquisition remains nominal.
    """
    validate_raw(compressed, sensor)
    if not np.isfinite(velocity_error) or abs(velocity_error) > 0.2:
        raise ValueError("velocity_error must be finite and within +/-0.2")
    x_m, y_m = np.asarray(x_m), np.asarray(y_m)
    if x_m.ndim != 1 or y_m.ndim != 1 or x_m.size * y_m.size > 200_000:
        raise ValueError("bounded 1D image axes required; max 200000 pixels")
    if not np.isfinite(x_m).all() or not np.isfinite(y_m).all():
        raise ValueError("image coordinates must be finite")
    eta, _, t = axes(sensor)
    xx, yy = np.meshgrid(x_m, y_m)
    focused = np.zeros(xx.shape, dtype=np.complex128)
    for pulse_index, time_s in enumerate(eta):
        px = time_s * sensor.velocity_m_s * (1 + velocity_error)
        r = np.sqrt((xx - px) ** 2 + yy**2 + sensor.altitude_m**2)
        delay = 2 * r / C_M_S
        line = compressed[pulse_index]
        values = np.interp(delay, t, line.real, left=0, right=0) + 1j * np.interp(
            delay, t, line.imag, left=0, right=0
        )
        focused += values * np.exp(4j * np.pi * r / sensor.wavelength_m)
    return focused / sensor.pulses


def direct_reference_pixel(raw, sensor: Sensor, x_m=0.0, y_m=1000.0):
    """Independent O(pulses*samples) raw-echo matched inner product at one pixel.

    Uses delay-specific chirps, bypassing compression and interpolation entirely.
    """
    validate_raw(raw, sensor)
    _, px, t = axes(sensor)
    r = np.sqrt((px - x_m) ** 2 + y_m**2 + sensor.altitude_m**2)
    template = chirp(t[None, :] - 2 * r[:, None] / C_M_S, sensor) * np.exp(
        -4j * np.pi * r[:, None] / sensor.wavelength_m
    )
    return np.vdot(template, raw) / np.vdot(template, template)
