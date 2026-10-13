# Four weeks inside SAR Observatory

The aim is to understand and modify the source without treating generated prose
as knowledge. Each exercise follows the same loop: write a prediction, change
one thing, regenerate, compare evidence and explain any disagreement. Save your
own notes in a new file rather than claiming authorship of work you cannot defend.

## Week one: geometry and coherent signals

Read config.py, simulator.py and math-to-code.md. Sketch platform/target
coordinates and derive R(η). Calculate centre delay, sample spacing and aperture
length by hand, then check `test_units_and_delay`. Explain phase cancellation
without looking at the code. Plot real/imaginary echoes and compare with magnitude.

**Exercise:** predict what happens to range width at B=20 MHz. Run the existing
`bandwidth-20` case, inspect ground width and compare the ratio with nominal.
Change `configs/demo.json` to 30 MHz, regenerate, record analytic versus measured
width and explain finite-chirp/interpolation differences. Restore the config afterward.

**Deliverable:** one-page explanation of delay versus phase, slant/ground geometry,
sampling versus resolution and the simulator's omitted physics.

## Week two: focusing and diagnostic behavior

Read focusing.py and metrics.py, then run the direct convolution and raw-reference
tests. Derive why time reversal and conjugation are both required. Locate where
range migration is handled. Explain each quality measure's units and window.

**Exercise:** before selecting residual +4 Hz, predict a displacement magnitude
fλR/(2v). Compare the actual peak and gate outcomes. Add a +2 Hz experiment in
`experiments.py`, regenerate and check the predicted half shift. Explain why the
width gate still passes and whether the current localization tolerance catches it.

**Extension:** implement a Hann aperture taper with proper gain normalization.
Predict broader mainlobe and lower sidelobes, add an independent weighting reference
and keep the untapered baseline. Do not change thresholds merely to force acceptance.

**Deliverable:** a notebook or written derivation explaining coherent integration,
model mismatch, width-only failure and finite-window sidelobe conventions.

## Week three: real products and inference limits

Read real-data.md, the source STAC records and earth.py. Explain gamma-zero,
linear power/dB, source RTC versus local resampling, product spacing versus resolution,
and why GRD-derived intensity has no interferometric phase. Run the real workflow
from the bundled crops and verify hashes.

**Exercise:** predict the direction of candidate-area changes at thresholds −19,
−17 and −15 dB. Compare the sensitivity table. Re-estimate Otsu after changing the
histogram bins to 128, record differences and explain why better class separation
does not imply validated water accuracy. Restore the baseline and regenerate.

**Evaluation exercise:** design, without fabricating results, a held-out study with
independent labels and temporal compatibility. Define calibration region, test region,
mask rules, uncertain-label exclusions, spatial units and reporting metrics.

**Deliverable:** a defensible interpretation of the actual lake result, including
the negative adaptive-threshold finding and every missing validation prerequisite.

## Week four: reliable software and interview defense

Read pipeline.py, pipeline-walkthrough.md, manifests, CI and browser tests. Trace
cache keys and understand why source/lock changes invalidate them. Run corrupted
input/cache tests. Explain process RSS sampling and machine-specific runtime limits.

**Exercise:** change a supported configuration, predict which hashes and files change,
run generation twice and explain the second run's cache logs. Deliberately tamper
only a temporary test cache via the provided test, observe recomputation and explain
why checksum verification matters. Do not corrupt the committed dataset.

Practice the five-minute script with a timer. Then conduct the twenty-minute source
walkthrough without notes. Answer follow-ups about FFT padding, phase signs, Otsu
transfer, registration and missing terrain masks. Repeat any topic you cannot derive.

**Deliverable:** your own demonstration recording and a skills-to-evidence revision
that clearly separates code reproduced/understood from remaining learning needs.

## First practical exercise

Predict the effect of halving bandwidth before opening the laboratory. Compare
nominal and 20 MHz: azimuth width should remain approximately constant while
ground-range width should approximately double. Read `test_bandwidth_and_aperture_scaling`,
run it with `uv run pytest -q -k bandwidth`, and explain the result in your own words.
