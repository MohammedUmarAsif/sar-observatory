# Code map

Start with the coordinate system, not with the web interface. Every numerical
module has one responsibility; presentation consumes immutable generated evidence.

```text
configs/demo.json -> config.Sensor
                    |                 data/source/*.json + data/*.tif
               simulator.simulate             |
                    |                       earth.analyze
            focusing.range_compress           |
                    |                         |
             focusing.backproject             |
                    |                         |
           metrics.assess + quality_gate       |
                    |                         |
              pipeline.run -------------------+
                    |
              experiments.generate
                    |
          results + site/assets + report
                    |
            site/app.js + science.mjs
```

## First five files

1. `src/sar_observatory/config.py`: units, sensor configuration, sampling validation.
2. `src/sar_observatory/simulator.py`: coordinates, delayed LFM chirps, complex phase, seeded noise.
3. `src/sar_observatory/focusing.py`: linear matched filtering, backprojection, independent reference.
4. `src/sar_observatory/metrics.py`: impulse widths, sidelobes, localization and gates.
5. `src/sar_observatory/pipeline.py`: stage contracts, content-addressed cache and provenance.

Then read `earth.py`, `experiments.py`, scientific tests and `site/science.mjs`.
The source browser lives on GitHub; documentation pages are statically built
from the Markdown files. `scripts/build_site.py` transforms notes without a server.

## Dependencies and safe changes

| Module | Inputs and outputs | Failure modes / validation / safe modification |
|---|---|---|
| config | SI-unit Sensor dataclass; analytic half-power widths | Rejects invalid values and supported-scene aliasing. `test_units_and_delay` and `test_sampling_configuration_rejected`. Change one parameter; keep fs ≥ 2B and PRF above Doppler support. |
| simulator | Sensor and target (x,y,complex amplitude) tuples -> complex128 [pulse,fast time] plus noise definition | Checks supported scene and echo truncation. Record-mean SNR includes empty range bins. Stop-and-go/flat terrain/constant amplitudes omit real radiometry. Noise-power and seed tests. Add scatterers only within checked extent; do not discard imaginary values. |
| focusing | complex128 echo -> compressed record -> complex [y,x] image | Range interpolation attenuates fractional-delay peaks; phase sign and reference energy matter. Direct convolution and raw-inner-product tests bypass the implementation. Increase fs or add a validated sinc interpolator before claiming higher accuracy. |
| metrics | uniform 1D metre axes + complex profiles; image + target truth -> metric dictionaries | Windows can truncate a response; noise produces unstable minima. Half-power crossings are interpolated in power. Sinc test supplies analytic PSLR and width evidence. Change gates through explicit design criteria rather than tuning to make failures pass. |
| pipeline | validated Sensor, optional externally supplied complex echo, experimental settings -> manifest + stage arrays | Nonfinite/real-valued/wrong-shape input stops before cache. Cache keys include raw/source/lock hashes. Cached NPZ file hash is verified. Performance is sampled process RSS, not exact allocation accounting. Modify stages without weakening provenance or validation. |
| earth | pinned unsigned STAC records + common-grid linear gamma-zero GeoTIFFs -> candidate masks and area statistics | Rejects CRS/grid mismatch and poor common coverage. No new calibration or terrain correction is performed. Positive finite intensity mask excludes source nodata; no explicit layover map is supplied. Threshold assumptions can fail badly. Maintain same-platform/orbit checks and validate a new AOI independently. |
| experiments | fixed config + seeds + licensed real crops -> machine-readable tables, plots, inventory and generated report | Point metrics deliberately use isolated targets; extended scene is only a qualitative example. Changing experiment definitions changes source hashes and invalidates cache. Regenerate the complete report after changes. |
| science.mjs/app.js | published JSON and native controls -> figures/readouts | Geometry is live; SAR cases are precomputed. Live water masks use averaged 40 m display values, unlike 10 m analysis. Node and browser tests check formulas and interactions. Preserve labels when changing data reduction or control behavior. |

## Reading exercise

Before executing anything, predict which exponential must be conjugated to
cancel carrier phase. Trace one target through `simulate`, `range_compress`,
`backproject` and `assess`. Explain why converting the raw array to `abs(raw)**2`
destroys the information required by the focuser. The rejection test supplies
a useful interview demonstration.
