# Design decisions

## One focuser, two independent checks

Direct backprojection makes exact delay and phase compensation inspectable.
It works for the small flat scene without a separate range-cell migration model.
Range-Doppler processing would be faster on larger regular grids, but would add
approximations and migration handling that are unnecessary here. Fast factorized
backprojection is related literature, not an implemented capability. The reference
is an independent raw-echo matched inner product, not a second copy of the same
interpolating algorithm. Direct convolution separately checks the FFT filter.

## Rectangular aperture and chirp

Rectangular weighting gives a transparent sinc baseline and visible sidelobes.
A taper could lower sidelobes at the cost of width and gain; it should be a new
controlled experiment, with analytic baselines and normalization checked. The
finite chirp has a bandwidth-duration product of 16 for the nominal case. It is
small enough for a demo, and its departures from asymptotic sinc behavior matter.

## Quality gates are educational design choices

The width multiplier 1.25 and localization tolerance 0.35 m are selected a priori
to demonstrate different error types. They are not StriX delivery specifications.
Width-only ablation is essential: linear phase can preserve sharpness while moving
the peak. Sidelobes are reported with windows and minima conventions; noisy minima
are not treated as robust mission-quality estimators. No learned classifier is added.

## Real-data choice

Two Poyang Lake Sentinel-1A orbit-40 acquisitions provide a seasonal/extreme-water
contrast with NASA contextual evidence. The bounded crop has 10 m pixels, not
10 m intrinsic resolution. Planetary Computer supplied Catalyst RTC and calibration;
the project does not repeat or claim those processing steps. Crops are bundled under
the collection's CC-BY-4.0 terms with Copernicus attribution and unsigned metadata.
Sen1Floods11 was rejected because an upstream redistribution licence could not be
verified. This limits independent accuracy evaluation, which is explicitly absent.

## Baseline and alternative

Fixed −17 dB VV is an intentionally simple sensitivity baseline, not a universal
water threshold. Otsu maximizes between-class histogram variance and does not
know which pixels are water. Re-estimating it per date can change class balance
and erase meaningful temporal contrast. This negative result is reported, not
hidden. A future reference-labeled experiment should compare a threshold estimated
on a separate calibration region, speckle-aware methods, and compatible labels.

## Static native web stack

HTML/CSS and small ES modules satisfy Pages constraints with no frontend framework,
router, Python service or bundle pipeline. The skill's React default is unnecessary
for the actual bounded interactions. Scientific diagrams use SVG for real geometry;
they are not decorative icons. Theme tokens provide system light/dark modes with
an optional manual choice. Plots retain their own white scientific figure surface.
Heavy scientific work is offline; parameter selectors select precomputed cases.
Live threshold masks use explicit display aggregation. Hash navigation and relative
assets support repository subpaths and refresh. Notes are built with Python Markdown.

## Reliability and tooling boundaries

uv locks exact dependency resolutions. Ruff formatting plus E/F/I/B/UP/SIM/NPY
rules and ty checking are used. The lint profile is intentionally targeted rather
than the skill's suggested ALL profile: scientific notation and untyped array
expressions should not be rewritten solely for style. Heterogeneous JSON records
use `Any` at the presentation boundary. Numerical behavior and provenance are
checked with tests rather than relying on static typing to validate physics.
Performance uses process RSS sampled every 10 ms; it is machine-specific and
includes native array allocations. It is neither exact high-water allocation
tracking nor a performance comparison with an optimized production processor.
