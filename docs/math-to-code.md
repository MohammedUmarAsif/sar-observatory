# Mathematics to code

## Coordinate system and dimensions

Cartesian coordinates in metres: platform `p(η)=(vη,0,h)`; scatterer
`q=(x,y,0)`. x is along track, y is ground range and z is up.
η is slow time in seconds; t is fast time in seconds. The ground is flat,
the platform is straight and velocity constant. This is a stop-and-go model:
motion during pulse propagation is neglected. Image arrays are `[y,x]`,
raw arrays `[pulse,fast-time sample]`. Sampling a complex baseband signal
does not mean sampling a real carrier at its microwave frequency.

## Equations, exact functions and checks

| Mathematics | Code | Independent/behavior check |
|---|---|---|
| Rⱼ(η)=sqrt((vη−xⱼ)²+yⱼ²+h²), τⱼ=2Rⱼ/c | `simulator.axes`, `simulator.simulate` | `test_units_and_delay` checks centre delay and sample spacings |
| p(u)=rect(u/T) exp(iπ(B/T)u²) | `simulator.chirp` | `test_complex_matched_filter_matches_direct_convolution` |
| s(η,t)=Σ aⱼ p(t−τⱼ) exp(−i4πRⱼ/λ) | `simulator.simulate` | `test_point_resolution_and_independent_reference` uses delay-specific raw templates |
| sᶜ=s * p*(−t), divided by Σ|p|² | `focusing.reference_chirp`, `range_compress` | NumPy full linear convolution reference, correctly trimmed by same mode |
| I(q)=N⁻¹ Σ sᶜ(η,2R(q,η)/c) exp(+i4πR(q,η)/λ) | `focusing.backproject` | Independent raw-echo inner product at target and off-target pixels |
| δr₋₃dB≈0.886 c/(2B); δy≈δr/sinθ | `config.Sensor.expected_widths` | bandwidth halving doubles measured ground width within stated numerical tolerance |
| δx₋₃dB≈0.886 λR/(2L) | same function | aperture halving and nominal-target tests |
| Δx≈fₑ λR/(2v) in small-angle broadside geometry | `simulate(doppler_hz=...)` | `test_doppler_shift_evades_width_gate`, magnitude and width checks |
| PSLR=10 log₁₀(max Pside/Ppeak) | `metrics.impulse_metrics` | analytic sinc-amplitude profile gives approximately −13.261 dB |
| ISLR=10 log₁₀(ΣPside/ΣPmain) | same function | finite-window sinc check; window explicitly differs from infinite integration |
| dB=10 log₁₀(γ⁰); area=count × pixel area | `earth.load_pair`, `analyze` | common-grid fixture, area accounting and provenance tests |
| σ²between=w₀w₁(μ₀−μ₁)² | `earth.otsu_threshold` | two-separated-population test, constant-histogram rejection |

The resolution factors assume rectangular weighting and approximately linear
spatial phase near broadside. They are half-power full widths; c/(2B) and
λR/(2L) without 0.886 are characteristic first-null spacings, not identical
width conventions. Finite chirp duration, interpolation, discrete aperture,
finite measurement windows and ground projection explain numerical differences.

## FFT and conjugation

The matched filter reverses time and conjugates complex phase. `fftconvolve`
implements **linear** convolution, including sufficient padding. It is not a
bare circular FFT product. An odd-length reference chirp preserves centre
alignment in `same` mode. NumPy's default FFT is unnormalized forward, inverse
normalized by transform length; changing normalization requires adjusting gain.
`np.vdot(template, raw)` conjugates its first argument and serves as the separate
delay-specific reference calculation. Complex interpolation applies to real and
imaginary components, never to phase angles wrapped at ±π.

## Impulse measurement conventions

P=|I|². Width crosses P/Ppeak=0.5 with linear interpolation on each side.
No interpolation-based increase in physical resolving power is claimed.
Cuts pass through the 2D peak; localization uses the nearest image-grid sample
relative to known isolated-target coordinates. The discretization allowance is
2dx for widths; the location is quantized to dx/2 and dy/2 per coordinate.
First neighboring local minima define the mainlobe; outside it, all samples in
the supplied window contribute to ISLR. Windows are x ±8 m and y ±30 m.
These are 1D cut metrics, not 2D sidelobe specifications. Discrete minima may
not coincide with exact analytic nulls, especially with noise or severe defocus.

## Noise, speckle and uncertainty

Injected circular complex Gaussian noise has E|n|²=σ²: each quadrature variance
is σ²/2. Record SNR is mean clean echo power over all recorded samples divided
by injected noise power. It is not focused target SNR or noise-equivalent sigma
zero. Independent seeded repetitions assess variability, not scene-wide speckle
statistics. The extended patch has random complex scatterer phases, but a proper
distributed-target speckle model needs many scatterers per resolution cell and
validated ensemble statistics. Real intensity includes source multilooking;
the simulator does not reproduce its equivalent number of looks.

Spatial-block resampling estimates heterogeneity within one fixed real crop.
It is not a flood-area accuracy confidence interval, and blocks may still be
correlated. Multiple block sizes expose sensitivity. Independent validation
requires temporally compatible reference labels and geographic holdouts.
