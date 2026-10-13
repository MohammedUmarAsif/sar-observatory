"""Complex baseband echoes with exact two-way delay and carrier phase."""

import numpy as np

from .config import C_M_S, Sensor


def axes(sensor: Sensor):
    """Return slow time [s], platform x [m], fast time [s]."""
    eta = (np.arange(sensor.pulses) - (sensor.pulses - 1) / 2) / sensor.prf_hz
    t = (
        2 * sensor.slant_m / C_M_S
        + (np.arange(sensor.range_samples) - sensor.range_samples // 2) / sensor.sample_rate_hz
    )
    return eta, eta * sensor.velocity_m_s, t


def chirp(dt, sensor: Sensor):
    """Unit-envelope rectangular LFM; dt is time relative to pulse center."""
    return (np.abs(dt) <= sensor.pulse_s / 2) * np.exp(
        1j * np.pi * (sensor.bandwidth_hz / sensor.pulse_s) * dt**2
    )


def scene(sensor: Sensor, extended=False):
    """Target tuples (x_m,y_m,complex reflectivity). Synthetic, uncalibrated."""
    if not extended:
        return [(0.0, sensor.center_ground_m, 1 + 0j)]
    targets = [(-3.0, 985.0, 1 + 0j), (0.0, 1000.0, 1 + 0j), (3.0, 1012.0, 0.8j)]
    rng = np.random.default_rng(sensor.seed)
    for x in np.linspace(1.5, 3.5, 5):
        for y in np.linspace(1018, 1024, 7):
            targets.append((float(x), float(y), 0.15 * np.exp(1j * rng.uniform(-np.pi, np.pi))))
    return targets


def simulate(sensor: Sensor, targets=None, snr_db=80.0, doppler_hz=0.0):
    """Echo shape (pulse,fast-time), complex128. SNR is record mean clean power/noise."""
    if not np.isfinite([snr_db, doppler_hz]).all():
        raise ValueError("SNR and Doppler must be finite")
    eta, platform_x, t = axes(sensor)
    raw = np.zeros((sensor.pulses, sensor.range_samples), dtype=np.complex128)
    for x, y, amplitude in scene(sensor) if targets is None else targets:
        if (
            not np.isfinite([x, y, amplitude]).all()
            or abs(x) > 8
            or abs(y - sensor.center_ground_m) > 30
        ):
            raise ValueError("target outside supported flat scene x +/-8, ground range +/-30 m")
        r = np.sqrt((platform_x - x) ** 2 + y**2 + sensor.altitude_m**2)
        delay = 2 * r / C_M_S
        if delay.min() - sensor.pulse_s / 2 < t[0] or delay.max() + sensor.pulse_s / 2 > t[-1]:
            raise ValueError("fast-time record truncates an echo; enlarge range_samples")
        raw += (
            amplitude
            * chirp(t[None, :] - delay[:, None], sensor)
            * np.exp(-4j * np.pi * r[:, None] / sensor.wavelength_m)
        )
    raw *= np.exp(2j * np.pi * doppler_hz * eta[:, None])
    clean_power = float(np.mean(np.abs(raw) ** 2))
    noise_power = clean_power * 10 ** (-snr_db / 10)
    rng = np.random.default_rng(sensor.seed)
    noise = np.sqrt(noise_power / 2) * (
        rng.standard_normal(raw.shape) + 1j * rng.standard_normal(raw.shape)
    )
    return raw + noise, {
        "clean_record_power": clean_power,
        "injected_noise_power": noise_power,
        "snr_db": snr_db,
        "doppler_hz": doppler_hz,
    }
