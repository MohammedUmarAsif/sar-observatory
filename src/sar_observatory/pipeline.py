"""Validated stages, content-addressed cache, structured logs and provenance."""

import json
import platform
import threading
import time
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

import numpy as np
import psutil

from .config import Sensor
from .focusing import backproject, image_axes, range_compress, validate_raw
from .metrics import assess, quality_gate
from .simulator import simulate

ROOT = Path(__file__).resolve().parents[2]


def checksum(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def array_checksum(array):
    return sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def write_json(path, value, *, compact=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=None if compact else 2, allow_nan=False) + "\n", encoding="utf-8"
    )


def source_hashes():
    return {p.name: checksum(p) for p in sorted(Path(__file__).parent.glob("*.py"))}


def log(stage, **fields):
    print(json.dumps({"stage": stage, **fields}, allow_nan=False))


def run(
    sensor: Sensor,
    *,
    snr_db=80.0,
    doppler_hz=0.0,
    velocity_error=0.0,
    targets=None,
    cache=True,
    raw_input=None,
):
    """Stages return arrays internally; persisted NPZ preserves complex I/Q.

    Corrupted input raises before any cache reuse. Cache keys include source,
    lock, config, experiment and echo digest; cached array files are verified.
    """
    raw, signal = (
        simulate(sensor, targets, snr_db, doppler_hz)
        if raw_input is None
        else (raw_input, {"source": "external complex input"})
    )
    validate_raw(raw, sensor)
    provenance = {
        "sensor": asdict(sensor),
        "snr_db": snr_db,
        "doppler_hz": doppler_hz,
        "velocity_error": velocity_error,
        "raw_sha256": array_checksum(raw),
        "source_sha256": source_hashes(),
        "lock_sha256": checksum(ROOT / "uv.lock"),
    }
    key = sha256(json.dumps(provenance, sort_keys=True).encode()).hexdigest()[:20]
    folder = ROOT / "artifacts" / "cache" / key
    manifest_path, arrays_path = folder / "manifest.json", folder / "stages.npz"
    if cache and manifest_path.exists() and arrays_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if checksum(arrays_path) == manifest["arrays_sha256"]:
            with np.load(arrays_path, allow_pickle=False) as stored:
                result = {name: stored[name] for name in stored.files}
            log("cache", key=key, verified=True)
            return manifest, result
        log("cache", key=key, verified=False, action="recompute")
    process = psutil.Process()
    baseline_rss = process.memory_info().rss
    samples = [baseline_rss]
    stop = threading.Event()

    def sample_memory():
        while not stop.wait(0.01):
            samples.append(process.memory_info().rss)

    worker = threading.Thread(target=sample_memory, daemon=True)
    worker.start()
    start = time.perf_counter()
    try:
        compressed = range_compress(raw, sensor)
        log("range_compression", key=key, shape=list(compressed.shape))
        x, y = image_axes(sensor)
        image = backproject(compressed, sensor, x, y, velocity_error)
        log("backprojection", key=key, shape=list(image.shape))
    finally:
        stop.set()
        worker.join()
        samples.append(process.memory_info().rss)
    runtime_s = time.perf_counter() - start
    metrics = assess(image, x, y)
    gate = quality_gate(metrics, sensor.expected_widths())
    manifest = {
        "schema": 1,
        "key": key,
        "provenance": provenance,
        "signal_definition": signal,
        "metrics": metrics,
        "gate": gate,
        "performance": {
            "compression_and_focus_s": runtime_s,
            "sampled_peak_rss_mib": max(samples) / 2**20,
            "incremental_peak_rss_mib": (max(samples) - baseline_rss) / 2**20,
            "rss_sampling_s": 0.01,
            "hardware": platform.processor() or platform.machine(),
            "os": platform.platform(),
            "python": platform.python_version(),
            "numpy": np.__version__,
            "cpu_count": psutil.cpu_count(),
        },
        "image_sha256": array_checksum(image),
    }
    result = {"raw": raw, "compressed": compressed, "image": image, "x_m": x, "y_m": y}
    folder.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(arrays_path, **result)
    manifest["arrays_sha256"] = checksum(arrays_path)
    write_json(manifest_path, manifest)
    log("quality", key=key, passed=gate["passed"], checks=gate["checks"])
    return manifest, result
