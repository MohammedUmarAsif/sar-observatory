# Interview guide

Use this portfolio as implemented evidence, not as a substitute for employment
experience. It was created with Codex assistance. Before presenting it, reproduce
the outputs yourself, inspect every numerical module and complete the exercises.
Say what you understand and what you are still learning. There is no Synspective
affiliation or claim of a novel algorithm, PhD thesis or production spaceborne processor.

## Five-minute demonstration

**0:00-0:45. Question and scope.** Open the observatory. Explain that one coherent
airborne-scale simulator connects geometry errors to automated image quality.
Real Sentinel-1 RTC is a separate intensity workflow. State the research question.

**0:45-1:45. Coherent formation.** Show the scene, raw echoes, matched filter and
focused scene. Explain delay versus carrier phase and why intensity alone cannot
be refocused. Show one equation mapped to a real source function and a test.

**1:45-2:45. Failure diagnosis.** Select velocity +3%, then residual Doppler +4 Hz.
Compare width and peak power, then localization. Explain why width-only acceptance
fails for a displaced but sharp target. Show the recorded corrupted-input rejection.

**2:45-3:45. Real scene.** Compare December/July VV intensity and the two candidate
water methods. Otsu's per-date threshold changes the inferred temporal contrast.
No labels means no accuracy score; contextual NASA evidence is not pixel truth.

**3:45-5:00. Defend and reproduce.** Open the report, manifest and code map.
Explain seeds, hashes, locked environment, analytic/direct references and block
resampling. Close with one limitation you could address next: independently
validated geometric registration or compatible water reference labels.

## Twenty-minute technical walkthrough

| Time | Repository evidence | Explain / challenge |
|---|---|---|
| 0-3 min | config.py + demo.json | Coordinates, fs/PRF, aperture definition, stop-and-go validity |
| 3-6 min | simulator.py | Range history, delayed chirp, carrier phase sign, complex Gaussian noise |
| 6-10 min | focusing.py + tests | Linear convolution, conjugation, normalization, fractional delay, direct reference |
| 10-13 min | metrics.py + profiles | Power versus amplitude, width convention, first-minimum windows, gate ablation |
| 13-16 min | pipeline.py + manifests | Input rejection, cache corruption, source/config/lock hashes, memory limitations |
| 16-19 min | earth.py + STAC records | Calibration supplied upstream, common grid, threshold failure, spatial dependence |
| 19-20 min | report + learning plan | Actual findings, honest authorship, missing evidence and next controlled study |

## Questions with grounded answers

**Why does a synthetic aperture improve azimuth resolution?** Coherent phase
changes across platform positions constrain a target's along-track coordinate.
The rectangular finite aperture produces an approximately sinc-shaped spatial
response. In our finite-aperture model width scales with λR/(2L); real stripmap
antenna-limited aperture length introduces the familiar antenna-length relation.

**Why is the echo phase −4πR/λ?** Round-trip distance is 2R. Carrier phase is
2π times path divided by wavelength, with the receive/baseband convention's
negative sign. Backprojection compensates with the opposite sign. State the
chosen convention rather than assuming every reference uses the same sign.

**Why a chirp instead of a short pulse?** It combines a longer energy-bearing
transmission with compressed delay resolution driven by bandwidth. Matched
filtering correlates with the known waveform; the nominal BT is modest and
finite-duration effects are visible. The project does not model transmitter power.

**Where is the FFT?** `scipy.signal.fftconvolve` performs range filtering efficiently
using padded transforms. The educational azimuth focuser uses direct geometric
summation; it is not a frequency-domain azimuth FFT processor. This avoids a false
claim about algorithms not implemented here.

**Why not use `abs(raw)` before focusing?** Magnitude discards the phase history.
Correct complex-number handling is central to coherent imaging; the pipeline
rejects detected intensity as raw input. SLC and GRD cannot be interchanged.

**What is range-cell migration?** Slant range changes over the aperture. A target's
echo moves in delay. Backprojection samples each predicted exact delay, so migration
is handled geometrically without a separate interpolation stage in range-Doppler space.

**Why does velocity error blur the target?** The assumed trajectory changes the
range curvature and predicted phase. Residual quadratic phase prevents coherent
summation. Width and peak power expose it. The fractional error is in the focuser;
the simulated acquisition is held fixed.

**Why can Doppler error keep an image sharp?** Linear slow-time phase changes
spatial phase slope and shifts the along-track peak. The small-angle predicted
shift magnitude fₑλR/(2v) agrees with the test; localization catches what width misses.

**What is resolution versus spacing?** Sampling grid spacing controls how densely
we describe an impulse response. It does not define physical resolution. Real
10 m RTC pixels derive from a GRD product with coarser source resolution metadata.

**Why ground-range resolution differs from slant?** Flat-ground projection divides
slant width by sin of incidence angle from vertical. Near nadir the ground projection
becomes ill-conditioned. The browser limits incidence to a reasonable range.

**How are PSLR and ISLR defined?** Both use power ratios in dB. PSLR uses the
strongest sidelobe sample; ISLR sums energy outside the first-minimum mainlobe
within a declared finite window. These 1D cuts are not interchangeable with a
mission's 2D quality specification or tapered processing convention.

**Is the simulator radiometrically calibrated?** No. Target amplitudes are arbitrary.
Carrier phase and delay are physical; gain, R⁻⁴ propagation loss, antenna pattern,
system transfer function and actual radar calibration are omitted. Peak power
compares controlled synthetic runs, not calibrated sigma-zero.

**How does noise differ from speckle?** Additive receiver noise is modeled as
circular complex Gaussian noise. Speckle arises from coherent scattering within
resolution cells and depends on ensemble and multilook statistics. The extended
patch illustrates interference but does not validate a complete speckle distribution.

**Why gamma-zero rather than sigma-zero here?** The real source delivers
terrain-corrected gamma-zero intensity. Respect that product's radiometric definition;
do not relabel it as sigma-zero. Conversion to dB uses 10log₁₀(power), not 20log₁₀.

**Can these real products yield interferometric coherence?** No. Detected RTC
intensity lacks valid complex phase. Interferometry needs compatible complex SLCs,
precise co-registration, geometry/baseline handling and phase-noise considerations.

**Is Otsu better than a fixed threshold?** This experiment cannot establish accuracy
without independent labels. Otsu selects class separation from each histogram; the
different thresholds drastically change temporal-area interpretation. Adaptivity
is a mechanism, not a guarantee of validity or improvement.

**Why not bootstrap every pixel?** Neighboring radar pixels are spatially dependent.
The project resamples paired blocks and compares block sizes. Those intervals describe
within-crop heterogeneity; they do not include label error, registration or algorithm bias.

**What happens to corrupt data?** Shape, complex dtype and finite-value validation
stop invalid raw input before processing. Cached files are hashed before reuse.
The test tampers a stage file and demonstrates recomputation, not silent use.

**How would you scale this?** Chunk/grid tiling, validated optimized backprojection
or an appropriate frequency-domain algorithm, calibrated numerical precision,
worker isolation, observability and explicit memory budgets. Benchmark complete
products on representative inputs before calling it a production architecture.

**What is numerically sensitive?** Carrier phase at large R/λ, fractional-delay
interpolation, chirp alignment, under-sampling, logarithms near zero and first-minimum
metrics in noisy profiles. Float64 complex processing limits phase error here;
mixed precision would require a new accuracy-versus-speed experiment.

## Challenging follow-ups

- Derive the linear-Doppler shift from the broadside range expansion, including sign.
- Predict the sidelobe and width tradeoff of Hann aperture weighting before coding it.
- Explain why the direct reference peak differs slightly from interpolated backprojection.
- Design a test that detects an accidental circular-convolution wraparound.
- Propose a rigorous threshold-transfer study using independent calibration/evaluation areas.
- Identify missing terrain masks and explain their possible effects on false candidates.
- Define how to certify geometric accuracy without known target truth in a real crop.
- Explain why block-size sensitivity does not prove residual spatial independence.
- Estimate computational complexity O(Npulse × Npixel) and memory allocation drivers.
- Describe what production experience and mission-specific knowledge this project does not establish.
