# Poyang Lake real-data case study

## What was acquired

The AOI is a 10.24 km square centered near 116.17° E, 29.10° N on a lake margin,
not the full lake. Source acquisition IDs:

- Before: `S1A_IW_GRDH_1SDV_20191205T101911_20191205T101936_030212_037408_rtc`
- After: `S1A_IW_GRDH_1SDV_20200708T101914_20200708T101939_033362_03DD85_rtc`

Both are Sentinel-1A, IW, GRD-derived Catalyst RTC, ascending relative orbit 40,
right-looking C-band. The acquisitions offer VV and VH; only VV is processed in
this case study. Complete STAC properties, timestamps, absolute orbit and unsigned
asset URLs are retained in `data/source/before.json` and `after.json`.
Nominal source GRD resolution metadata is 20 m in range and 22 m in azimuth;
10 m output spacing is not intrinsic resolving power.

## Supplied versus performed processing

The collection documentation says Catalyst converted GRD to calibrated intensity,
applied gamma-zero correction, radiometrically corrected terrain using PlanetDEM
and orthorectified to UTM. Those operations were **supplied by the source**.
The referenced correction basis is Small's 2011 Flattening Gamma paper.
We did not rerun or independently certify that processing history, DEM or orbit correction.

Locally, `earth.fetch` reads bounded COG windows, checks UTM zone 50N and crop
containment, and uses bilinear resampling onto one fixed 1024 × 1024, 10 m grid.
The crops' common-grid identity is verified before comparison. This is raster
grid alignment, not an independently validated subpixel image-registration result.
The source grid origins are not guaranteed identical. Use features or external
control points to quantify residual geolocation errors before an accuracy claim.

The mask requires finite, positive power on both dates and excludes nodata.
Source shadow handling is described in the collection, but explicit layover,
shadow, incidence-angle and thermal-noise masks are not available in these bundled
assets. The flat lake setting reduces some terrain risks without eliminating them.
No local speckle filter is applied: preserve a clear threshold baseline and document
the source multilook information. All local software versions and crop hashes are
published in `results/earth.json` and the artifact inventory.

## Methods and evaluation design

Convert linear gamma-zero to dB using 10 log₁₀. Compare a fixed VV < −17 dB
baseline to per-date Otsu with 256 bins over [−40,5] dB. Histogram tails outside
that interval do not affect threshold estimation but still receive classifications.
Count candidate pixels over the common valid mask and multiply by 100 m².
Study sensitivity across fixed thresholds −19 to −15 dB and spatial block sizes
640,1280,2560 m. Paired resampling retains the same blocks on both dates, with
1000 seeded bootstrap repetitions. This samples within-AOI heterogeneity; it is
not a spatially independent pixel-based uncertainty calculation.

There are no verified independent pixel reference labels for this AOI/date pair.
Consequently we do not report IoU, precision, recall, flood area or an accuracy
improvement. NASA's Poyang Lake Extremes article provides wider high-water context
from different optical dates. Temporal mismatch and source differences prohibit
treating it as pixel-level ground truth. Future evaluation needs compatible
optical/manual/emergency-mapping labels, cloud/vegetation ambiguity handling and
geographically independent holdout regions. Threshold selection must not use the
same evaluation labels it is assessed against.

## Interpretation and limits

The fixed and adaptive methods strongly disagree about temporal extent. Otsu's
class-balance dependence is an observed limitation in this crop, not evidence that
the fixed threshold is accurate. Seasonal water change is visible and contextualized;
dark candidates are not individually confirmed flood pixels. Speckle, wind-roughened
water, wet soils and inundated vegetation can invalidate intensity-only assumptions.
Block sensitivity intervals depend on block size and spatial stationarity; residual
correlation remains possible. Results cannot be generalized to the entire lake or
other missions, seasons and orbit geometries.

## Attribution and redistribution

Contains modified Copernicus Sentinel data 2019 and 2020. Catalyst RTC via
Microsoft Planetary Computer. Collection metadata declares CC-BY-4.0:
[source collection and processing history](https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-1-rtc),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/),
[Copernicus Sentinel notice](https://cds.climate.copernicus.eu/licences/ec-sentinel).
The project's code licence does not relicense upstream imagery. Bundled crops
are small derived subsets, with georeferencing and SHA-256 retained.

## Why the synthetic and real branches differ

Synthetic echoes preserve complex I/Q and can be refocused under controlled model
errors. Real RTC intensity has already been focused, detected, multilooked,
calibrated and terrain corrected upstream. It cannot be refocused by this simulator
or provide interferometric phase/coherence. The branches share disciplined validation
and provenance, not the same numerical processor or sensor configuration.
