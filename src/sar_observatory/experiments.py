"""One command regenerates every published scientific figure and table."""

import argparse
import json
from dataclasses import replace
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from .config import Sensor
from .earth import analyze
from .focusing import direct_reference_pixel
from .pipeline import ROOT, checksum, run, write_json
from .report import create_report
from .simulator import scene

ASSETS = ROOT / "site" / "assets"


def power_db(array):
    p = np.abs(array) ** 2
    return 10 * np.log10(np.maximum(p / max(float(p.max()), 1e-30), 1e-6))


def save_image(data, filename, *, extent, xlabel, ylabel, label, cmap="gray", vmin=-45, vmax=0):
    fig, ax = plt.subplots(figsize=(7, 4.3), layout="constrained")
    shown = ax.imshow(
        data, origin="lower", extent=extent, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax
    )
    ax.set(xlabel=xlabel, ylabel=ylabel)
    fig.colorbar(shown, ax=ax, label=label)
    fig.savefig(ASSETS / filename, dpi=130)
    plt.close(fig)


def generate(cache=True):
    ASSETS.mkdir(parents=True, exist_ok=True)
    config = json.loads((ROOT / "configs" / "demo.json").read_text(encoding="utf-8"))
    nominal = Sensor(**config)
    variants = [
        ("nominal", "Correct model", nominal, {}),
        ("velocity-1", "Velocity +1%", nominal, {"velocity_error": 0.01}),
        ("velocity-3", "Velocity +3%", nominal, {"velocity_error": 0.03}),
        ("velocity-6", "Velocity +6%", nominal, {"velocity_error": 0.06}),
        ("doppler", "Residual Doppler +4 Hz", nominal, {"doppler_hz": 4.0}),
        ("noise-25", "Record SNR -25 dB", nominal, {"snr_db": -25.0}),
        ("noise-15", "Record SNR -15 dB", nominal, {"snr_db": -15.0}),
        ("noise-5", "Record SNR +5 dB", nominal, {"snr_db": 5.0}),
        ("bandwidth-20", "Bandwidth 20 MHz", replace(nominal, bandwidth_hz=20e6), {}),
        ("bandwidth-60", "Bandwidth 60 MHz", replace(nominal, bandwidth_hz=60e6), {}),
        ("aperture-32", "Aperture 32 m", replace(nominal, pulses=256), {}),
    ]
    cases: list[dict[str, Any]] = []
    baseline_arrays = None
    for key, label, sensor, settings in variants:
        manifest, arrays = run(sensor, cache=cache, **settings)
        image, x, y = arrays["image"], arrays["x_m"], arrays["y_m"]
        iy, ix = np.unravel_index(np.argmax(np.abs(image)), image.shape)
        case = {
            "id": key,
            "label": label,
            "manifest": manifest,
            "expected": sensor.expected_widths(),
            "azimuth_profile_db": np.round(power_db(image[iy, :]), 3).tolist(),
            "ground_profile_db": np.round(power_db(image[:, ix]), 3).tolist(),
            "x_m": x[::2].tolist(),
            "profile_x_m": x.tolist(),
            "ground_offset_m": (y - sensor.center_ground_m).tolist(),
        }
        cases.append(case)
        save_image(
            power_db(image),
            f"{key}.png",
            extent=[x[0], x[-1], y[0] - 1000, y[-1] - 1000],
            xlabel="Along-track x [m]",
            ylabel="Ground-range offset [m]",
            label="Power relative to each image peak [dB]",
            cmap="viridis",
            vmin=-45,
        )
        if key == "nominal":
            baseline_arrays = arrays
            case["independent_reference"] = {
                "raw_inner_product_abs": float(abs(direct_reference_pixel(arrays["raw"], sensor))),
                "backprojection_peak_abs": float(np.abs(image).max()),
            }
    # Independent scenes keep point-target metrics uncontaminated by neighbors.
    _, extended = run(nominal, targets=scene(nominal, extended=True), cache=cache)
    save_image(
        power_db(extended["image"]),
        "extended.png",
        extent=[-8, 8, -30, 30],
        xlabel="Along-track x [m]",
        ylabel="Ground-range offset [m]",
        label="Synthetic scene power [dB relative to peak]",
        cmap="viridis",
    )
    assert baseline_arrays is not None, "nominal case must be generated"
    raw = baseline_arrays["raw"]
    for data, filename, label in [
        (extended["raw"], "raw.png", "Raw complex echo power [dB relative]"),
        (extended["compressed"], "compressed.png", "Compressed power [dB relative]"),
    ]:
        save_image(
            power_db(data),
            filename,
            extent=[0, nominal.range_samples, -0.32, 0.32],
            xlabel="Fast-time sample index",
            ylabel="Slow time [s]",
            label=label,
        )
    # Scene coordinates, rather than a fake satellite photograph.
    fig, ax = plt.subplots(figsize=(7, 4.3), layout="constrained")
    targets = scene(nominal, extended=True)
    ax.scatter(
        [t[0] for t in targets],
        [t[1] - 1000 for t in targets],
        c=[abs(t[2]) for t in targets],
        cmap="viridis",
    )
    ax.set(
        xlim=(-8, 8), ylim=(-30, 30), xlabel="Along-track x [m]", ylabel="Ground-range offset [m]"
    )
    fig.savefig(ASSETS / "scene.png", dpi=130)
    plt.close(fig)
    # Repeated-seed paired trials: same clean scene, independent noise realizations.
    repetitions = []
    for seed in range(101, 107):
        trial, _ = run(replace(nominal, seed=seed), snr_db=-25, cache=cache)
        repetitions.append(
            {
                "seed": seed,
                "azimuth_width_m": trial["metrics"]["azimuth"]["width_m"],
                "localization_m": trial["metrics"]["localization_m"],
                "peak_power": trial["metrics"]["peak_power"],
                "passed": trial["gate"]["passed"],
            }
        )
    widths = [r["azimuth_width_m"] for r in repetitions]
    summary = {
        "seeded_trials": repetitions,
        "snr_db": -25,
        "width_mean_m": float(np.mean(widths)),
        "width_sd_m": float(np.std(widths, ddof=1)),
        "width_empirical_range_m": [min(widths), max(widths)],
        "warning": "Six trials characterize this simulator; not a population confidence interval.",
    }
    # Ablation: a width-only gate misses linear-phase localization failures.
    doppler = next(c for c in cases if c["id"] == "doppler")
    ablation = {
        "width_only_accepts_doppler": doppler["manifest"]["gate"]["checks"]["width"],
        "full_gate_accepts_doppler": doppler["manifest"]["gate"]["passed"],
    }
    corruption = raw.copy()
    corruption[0, 0] = np.nan
    try:
        run(nominal, raw_input=corruption)
    except ValueError as exc:
        rejected = {
            "input": "complex echo with injected NaN at [0,0]",
            "outcome": "rejected before processing",
            "message": str(exc),
        }
    else:
        raise AssertionError("corrupted input was accepted")
    output = {
        "schema": 1,
        "question": "Which diagnostics distinguish velocity defocus from Doppler displacement?",
        "cases": cases,
        "noise_repetitions": summary,
        "gate_ablation": ablation,
        "corrupted_input": rejected,
        "interpretation": "All laboratory data are synthetic.",
    }
    write_json(ROOT / "results" / "synthetic.json", output)
    write_json(ASSETS / "synthetic.json", output, compact=True)
    earth, db, valid, masks = analyze()
    for index, name in enumerate(("before", "after")):
        # Raster rows are north to south; flip for lower-origin scientific plotting.
        extent = [0, valid.shape[1] * 10 / 1000, 0, valid.shape[0] * 10 / 1000]
        save_image(
            np.flipud(np.where(valid, db[index], np.nan)),
            f"earth-{name}.png",
            extent=extent,
            xlabel="Easting offset [km]",
            ylabel="Northing offset [km]",
            label="VV gamma-zero [dB]",
            vmin=-30,
            vmax=0,
        )
        plt.imsave(
            ASSETS / f"earth-{name}-texture.jpg",
            np.where(valid, db[index], np.nan),
            cmap="gray",
            vmin=-30,
            vmax=0,
        )
        for width in (480, 768):
            with Image.open(ASSETS / f"earth-{name}-texture.jpg") as texture:
                texture.resize((width, width), Image.Resampling.LANCZOS).save(
                    ASSETS / f"earth-{name}-texture-{width}.jpg", quality=78, progressive=True
                )
                texture.resize((width, width), Image.Resampling.LANCZOS).save(
                    ASSETS / f"earth-{name}-texture-{width}.webp", quality=65, method=6
                )
        for method in ("fixed", "otsu"):
            save_image(
                np.flipud(np.where(valid, masks[method][index], np.nan)),
                f"earth-{name}-{method}.png",
                extent=extent,
                xlabel="Easting offset [km]",
                ylabel="Northing offset [km]",
                label="Candidate water (1); other valid pixels (0)",
                cmap="Greens",
                vmin=0,
                vmax=1,
            )
    write_json(ASSETS / "earth.json", earth)
    # Display-ready arrays enable truly live bounded threshold calculation.
    # 4x4 power averaging is explicitly a display reduction, not analysis resolution.
    display = [
        10 * np.log10(np.mean(10 ** (d / 10).reshape(256, 4, 256, 4), axis=(1, 3))) for d in db
    ]
    write_json(
        ASSETS / "earth-display.json",
        {
            "db": [np.round(d, 2).tolist() for d in display],
            "valid": valid.reshape(256, 4, 256, 4).all(axis=(1, 3)).astype(int).tolist(),
            "pixel_m": 40,
            "description": "4x4 power mean for display; analysis uses 10 m inputs",
        },
        compact=True,
    )
    # One figure for the coherent experiment comparison.
    fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
    for case in cases[:5]:
        ax.plot(case["profile_x_m"], case["azimuth_profile_db"], label=case["label"])
    ax.set(
        xlim=(-2, 2), ylim=(-45, 1), xlabel="Along-track x [m]", ylabel="Peak-normalized power [dB]"
    )
    ax.legend(fontsize=8)
    fig.savefig(ASSETS / "profiles.png", dpi=150)
    plt.close(fig)
    create_report(output, earth)
    inventory = {
        "source": "uv run python -m sar_observatory.experiments",
        "files": {
            str(p.relative_to(ROOT)).replace("\\", "/"): checksum(p)
            for folder in (ROOT / "results", ROOT / "data", ASSETS)
            for p in sorted(folder.rglob("*"))
            if p.is_file() and p.name != "inventory.json"
        },
    }
    write_json(ROOT / "results" / "inventory.json", inventory)
    write_json(ASSETS / "inventory.json", inventory)
    print(
        json.dumps(
            {
                "cases": len(cases),
                "ablation": ablation,
                "noise": summary,
                "nominal": cases[0]["manifest"]["metrics"],
                "earth": earth["methods"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args()
    generate(cache=not args.no_cache)
