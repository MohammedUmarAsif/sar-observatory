# Research brief

Access date for all links: 2026-10-13. Facts below were checked against primary
sources. Implementation choices are identified separately. No Synspective
affiliation, employment history, production experience or original research is claimed.

## Verified career evidence

[SAR Image Processing Engineer](https://careers.synspective.com/o/sar-image-processing-engineer)
describes pipeline architecture, algorithm integration, signal/geometry issue
investigation and automated product verification. It asks for SAR/DSP foundations,
maintainable scientific software and prior production ownership. This portfolio
can evidence implemented fundamentals; it cannot substitute for that employment experience.

[SAR research engineer](https://careers.synspective.com/o/kr8lcfsbty) emphasizes
literature investigation, technical hypotheses, prototypes and validation.
This is a paraphrase/interpretation of the Japanese public description.

| Requirement/theme | Component | Reviewable evidence |
|---|---|---|
| Coherent formation and DSP | Complex delayed chirps, linear matched filter, backprojection | simulator.py, focusing.py, scientific tests |
| Signal/geometry troubleshooting | Velocity and residual Doppler sweeps | experiments.py, results/synthetic.json, failure atlas |
| Automated product verification | Width/localization gates, rejected inputs | pipeline.py, manifests, failure test |
| Maintainable processing software | Configuration validation, stage contracts, cache integrity | config.py, pipeline.py, CI |
| Calibration and geometry | Real gamma-zero intensity on common UTM grid | earth.py, real manifest |
| Hypothesis testing and reporting | Controlled sweeps, noise repetitions, independent calculations | report.md, tests, provenance |

## Verified technical sources

- [Synspective product descriptions](https://www.synspective.com/data/synspective-sar-data/): distinguishes complex SLC and detected/geocoded product formats. Product-specific capabilities are not implemented here.
- [Current document hub](https://www.synspective.com/document/) lists product guide v19.0 and format manual v21.2. [Format manual v21.2](https://www.synspective.com/files/co/document-files/SAR-Data-Product-Format-Manual_EN_v21-2.pdf), dated 2026-09-16, includes product-specific calibration and processor-version metadata. This reinforces provenance/version checking; the project does not implement its proprietary product interfaces. Older indexed product-guide URLs returned 404 and were replaced with these checked primary pages.
- [ESA ERS coherent imaging](https://www.esa.int/esapub/bulletin/bullet83/fran83.htm): chirp compression and coherent aperture integration underpin resolution.
- [ESA/DLR SAR training](https://seom.esa.int/landtraining2015/files/Day_1/D1T1b_LTC2015_Younis.pdf): range bandwidth and aperture-based azimuth resolution. Rectangular weighting is the project's analytic baseline.
- [DLR signal processing](https://www.dlr.de/de/hr/ueber-uns/abteilungen/sar-technologie/sar-signalverarbeitung): identifies backprojection among operational research algorithms. Our implementation is direct, not fast factorized.
- [Copernicus S1 processing](https://sentiwiki.copernicus.eu/web/s1-processing): real GRD and SLC have different processing and phase properties.
- [ASF RTC guide](https://hyp3-docs.asf.alaska.edu/guides/rtc_product_guide/): describes geometric/radiometric corrections and DEM requirements. ASF GAMMA processing is background; the selected Planetary Computer source instead uses Catalyst.
- [NASA Poyang Lake Extremes](https://science.nasa.gov/earth/earth-observatory/poyang-lake-extremes-146987/): credible context for contrasting late-2019 and July-2020 lake conditions. Its optical observations are contextual evidence, not pixel truth for our dates.
- [Planetary Computer RTC collection metadata](https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-1-rtc): calibrated gamma-zero, Catalyst RTC using PlanetDEM, UTM orthorectification, collection CC-BY-4.0. Exact acquisition properties are retained in data/source/*.json.
- [Small 2011, Flattening Gamma](https://ai4edatasetspublicassets.blob.core.windows.net/assets/pdfs/sentinel-1/2011_Flattening_Gamma.pdf): primary radiometric terrain-correction basis linked by the collection.
- [Copernicus licence](https://cds.climate.copernicus.eu/licences/ec-sentinel): open use with required source attribution. Derived imagery is attributed as containing modified Copernicus Sentinel data.
- [NumPy FFT](https://numpy.org/doc/stable/reference/routines.fft.html), [SciPy fftconvolve](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.fftconvolve.html), [Rasterio windows](https://rasterio.readthedocs.io/en/stable/topics/windowed-rw.html): conventions and public APIs checked, including via Context7.
- [uv](https://docs.astral.sh/uv/), [Ruff](https://docs.astral.sh/ruff/), [pytest](https://docs.pytest.org/en/stable/), [GitHub Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages): reproducible environment, bounded checks and static deployment.

## Research question and scope (design choices)

How do controlled platform-velocity mismatch and uncompensated linear Doppler
phase affect point-target impulse response and localization, and which automated
diagnostics distinguish defocus from displacement?

Hypothesis: quadratic phase mismatch broadens the impulse response; linear phase
can shift a sharp peak and evade width-only acceptance. This connects focusing
to product reliability without claiming a spaceborne processor or a new algorithm.

Implement a straight, constant-altitude, broadside, stop-and-go stripmap model
with a rectangular finite aperture, a small scene and constant scatterer amplitudes.
Use a single backprojection algorithm with a direct raw-echo matched inner product
as its independent reference. Ignore Earth curvature, atmospheric propagation,
antenna gain variation, actual instrument calibration and motion during a pulse.
No InSAR, deep learning, proprietary StriX data or satellite telemetry.

## Data and deployment constraints

Real study: bounded Poyang Lake VV/VH RTC crops; select same platform/relative
orbit and retain identifiers. Source products have already been calibrated and
terrain corrected. Locally crop/regrid, mask invalid intensities and compare
fixed VV threshold with histogram Otsu. No independent contemporaneous labels
have yet been verified; report candidate-water extent and method sensitivity,
not flood accuracy. Spatial blocks, not pixels, define resampling units.
Sen1Floods11 was considered but rejected because its upstream licence file could
not be verified. Do not redistribute its labels.

Anonymous RTC signing/access will be tested before committing to the case.
Read bounded COG windows rather than multi-GB scenes; retain unsigned source
URLs, never ephemeral tokens. Bundle small licensed crops for credential-free
reproduction. Static Pages serves compact generated artifacts; scientific work
runs offline/CI. Browser controls select independently generated experiment
variants; geometry formulas alone calculate live. Native static assets and
hash links avoid server routing and repository-subpath errors.

## Validation strategy

Check analytic rectangular-aperture sinc expectations, chirp width ~0.886 c/(2B),
azimuth width ~0.886 lambda R/(2L), FFT versus direct convolution and direct
raw-echo reference; perturbations, complex inputs, corrupted data and cache hashes.
Widths use half-power crossings; sidelobes use first-minimum boundaries and a
fixed measurement window. Repeat seeded noise trials and publish effect sizes
and empirical uncertainty. Bound processing memory and grids. Regenerate all
tables/figures; retain config, dependency lock hash, source hashes and machine
details. Verify real CRS, overlap, masks, units and acquisition geometry.
Inspect deployed site at desktop/mobile and test controls, citations and paths.

Additional checked primary/library references:
- [Ulander, Hellsten and Stenstrom, 2003](https://research.chalmers.se/en/publication/6728): related fast factorized backprojection paper, DOI 10.1109/TAES.2003.1238734; bibliographic context, not the implemented optimization.
- [Otsu, 1979](https://ieeexplore.ieee.org/document/4310076): threshold selection by between-class variance, DOI 10.1109/TSMC.1979.4310076; bibliographic record checked, local histogram equation implemented independently.
- [Playwright assertions](https://playwright.dev/docs/test-assertions), [Python Markdown](https://python-markdown.github.io/), [MDN ES modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules): static-note generation and browser checks.
