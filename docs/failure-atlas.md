# Failure atlas

Values and figures are generated in the [research report](report.md).

| Trigger | Symptom | Useful diagnostics | What can mislead | Remedy / next experiment |
|---|---|---|---|---|
| Assumed velocity differs from true velocity | Residual quadratic phase; defocus and coherent loss | Width, peak power, sidelobe profile | Peak normalization hides coherent loss | Inspect motion model, estimate Doppler rate, rerun geometry sweep |
| Residual +4 Hz linear Doppler phase | Sharp peak moves along track | Localization relative to known target | Width passes; image looks sharp | Estimate/compensate centroid and verify geometric truth |
| Additive complex noise | Higher sidelobe/background variability | Repeated seeded trials, raw noise definition | Six trials or one peak are not population evidence; coherent averaging reduces noise | More seeds, lower SNR, prespecified diagnostics and false-positive study |
| Bandwidth decreases | Range response widens | Ground/slant half-power width with bandwidth baseline | Treating pixel spacing as resolution | Increase bandwidth only with sufficient sampling and chirp support |
| Aperture decreases | Azimuth width increases | Aperture-dependent analytic width | Absolute width threshold would reject a valid short-aperture product | Condition acceptance on actual acquisition parameters |
| Low PRF | Supported Doppler aliases | Sampling checks reject configuration | Peak shape may still look plausible | Raise PRF or reduce supported aperture/scene; do not bypass validator |
| Real-valued intensity supplied as raw | Missing carrier phase | Complex-dtype validation | Detected pixels cannot recover I/Q | Obtain valid complex input; use intensity workflow separately |
| NaN injected into echo | Invalid FFT/phase calculations | Pre-stage finite-value check | Downstream normalizers can conceal invalid values | Fail before compression with explicit location/context |
| Cached NPZ tampered | Untrusted stage content | Manifest SHA-256 mismatch | A filename alone is not provenance | Recompute that case; preserve source/config/lock hashes |
| Otsu fitted independently to changing scenes | Threshold shifts with histogram balance | Per-date thresholds, disagreement, paired area change | Adaptive does not mean more accurate | Validate with compatible reference labels; use prespecified transfer threshold |
| Dark SAR return | Apparent water extent | Geometry masks, external evidence, temporal context | Shadow, wet soil, smooth land and wind effects | Call it candidate water until independently confirmed |

## Corrupted-input demonstration

`experiments.generate` inserts a NaN at raw[0,0]. The actual pipeline rejects it
with `echo contains NaN/Inf; stop before range compression`. The website shows
this recorded result, not a fake live server response. Scientific tests also
reject real-valued and wrong-shape inputs.

## Where simple diagnostics fail

Peak width cannot establish geometric accuracy: linear Doppler phase moves a sharp
response. Peak-normalized plots cannot establish radiometric consistency: every
image's strongest sample is mapped to 0 dB. A threshold-derived area cannot establish
flood extent: the labels and physics of water/other dark surfaces are unresolved.
These failures motivate combining physically distinct checks rather than one score.
