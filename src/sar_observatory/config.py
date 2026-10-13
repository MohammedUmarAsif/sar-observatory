"""Coordinates: x along track, y ground range, z up; flat targets at z=0."""

import math
from dataclasses import asdict, dataclass

C_M_S = 299_792_458.0


@dataclass(frozen=True)
class Sensor:
    wavelength_m: float = 0.03
    altitude_m: float = 1000.0
    center_ground_m: float = 1000.0
    velocity_m_s: float = 100.0
    bandwidth_hz: float = 40e6
    sample_rate_hz: float = 160e6
    pulse_s: float = 0.4e-6
    prf_hz: float = 800.0
    pulses: int = 512
    range_samples: int = 512
    seed: int = 17

    def __post_init__(self):
        for key, value in asdict(self).items():
            if key != "seed" and (not math.isfinite(value) or value <= 0):
                raise ValueError(f"{key} must be finite and positive")
        if not isinstance(self.pulses, int) or not isinstance(self.range_samples, int):
            raise ValueError("sample counts must be integers")
        if self.sample_rate_hz < 2 * self.bandwidth_hz:
            raise ValueError("fast-time sampling must be >= 2B for this laboratory")
        if self.pulses > 2048 or not 128 <= self.range_samples <= 2048:
            raise ValueError("bounded laboratory: pulses <=2048; range samples 128..2048")
        if self.pulses < 64 or self.pulse_s * self.sample_rate_hz < 8:
            raise ValueError("insufficient aperture or chirp samples")
        if self.pulse_s * self.sample_rate_hz > self.range_samples / 3:
            raise ValueError("chirp must fit inside the recorded fast-time interval")
        # Worst Doppler in the supported scene x +/-8 m, y center +/-30 m.
        nearest_r = math.hypot(self.altitude_m, self.center_ground_m - 30)
        fd_max = 2 * self.velocity_m_s * (self.aperture_m / 2 + 8) / (self.wavelength_m * nearest_r)
        if self.prf_hz <= 2 * fd_max:
            raise ValueError("azimuth aliasing: PRF must exceed twice supported Doppler")

    @property
    def slant_m(self):
        return math.hypot(self.altitude_m, self.center_ground_m)

    @property
    def aperture_m(self):
        return self.pulses * self.velocity_m_s / self.prf_hz

    @property
    def incidence_rad(self):
        return math.atan2(self.center_ground_m, self.altitude_m)

    def expected_widths(self):
        return {
            "slant_m": 0.886 * C_M_S / (2 * self.bandwidth_hz),
            "ground_m": 0.886 * C_M_S / (2 * self.bandwidth_hz * math.sin(self.incidence_rad)),
            "azimuth_m": 0.886 * self.wavelength_m * self.slant_m / (2 * self.aperture_m),
        }
