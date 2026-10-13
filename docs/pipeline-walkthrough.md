# One input through the pipeline

Run `uv run python -m sar_observatory.experiments --no-cache` from the repository.

1. `configs/demo.json` creates a validated Sensor: X-band-like 0.03 m wavelength,
   1 km altitude, 1 km ground range, 100 m/s velocity and a finite 64 m aperture.
   These are chosen educational parameters, not a real mission configuration.
2. `scene` places an isolated unit complex target at (0,1000,0) m. `axes` creates
   slow-time pulses about zero and fast-time samples about the centre delay.
3. `simulate` evaluates exact Euclidean slant range at each pulse, delays the
   LFM waveform, adds two-way carrier phase and deterministically seeded noise.
4. `validate_raw` checks shape, complex dtype and finite values. The corrupted
   example injects NaN at [0,0] and is rejected here, before compression or cache.
5. `range_compress` convolves every pulse with the reversed conjugate transmit
   chirp. This is a linear, energy-normalized filter; phase remains available.
6. `backproject` predicts each pixel's delay and carrier phase, interpolates
   complex samples and averages coherently over pulses. Its output is not yet
   calibrated radar backscatter. The image is an arbitrary-reflectivity simulation.
7. `assess` measures cuts through the peak. `quality_gate` applies explicit
   educational thresholds based on analytic width and known target position.
8. `run` saves complex NPZ stages and a manifest under `artifacts/cache/<key>`.
   Its key incorporates source hashes, lock hash, configuration and raw-echo hash.
   A reused stage file must match its saved SHA-256. A corrupted cache recomputes.
9. `experiments.generate` publishes numerical records in `results/synthetic.json`
   and plot assets in `site/assets`. The real-data branch joins at this artifact
   layer; no real intensity is routed into the complex simulator focuser.
10. `app.js` fetches immutable experiment records and selects an existing
    image/profile. Browser geometry and reduced-grid thresholding are separately
    labeled live calculations. `scripts/build_site.py` renders Markdown notes.

## Restart and inspection

Rerunning the generation command without `--no-cache` reuses verified cached
numerical stages while regenerating presentation artifacts. There is no scheduler,
distributed worker or operational downlink ingestion. Whole-case caching is
justified by the small deterministic stages; finer checkpoints would add complexity
without meaningful benefit. Remove only a specific cache entry to force that case.
Caches are not committed; published outputs and crops are. Logs are JSON lines
with stage names, shapes, case keys and gate outcomes. Performance measurements
describe the original numerical run retained in a cache manifest.

## Trace exercise

Find the nominal case's raw-echo checksum in `results/synthetic.json`. Follow
its manifest into the file hashes and then find the profile consumed by `app.js`.
Change the velocity error to 0.01, predict what happens to coherent peak power,
run the generator and explain which gate changed. Never edit JSON results by hand.
