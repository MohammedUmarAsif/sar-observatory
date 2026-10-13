# Verification evidence

Checked 2026-10-13. Local Windows host; Python 3.12.5, locked dependencies.

- 23 scientific/pipeline tests pass; 86% statement coverage, with a required 80% floor.
- Analytic width/sinc checks, direct convolution, independent raw matched inner product.
- Velocity defocus, Doppler displacement, noise and bandwidth/aperture behavior checks.
- Corrupt echo rejection, tampered-cache recomputation, real grid-mismatch rejection.
- Complete generated-artifact test verifies inventory SHA-256 values.
- Ruff lint/format and ty pass. Source hashes match current published manifests.
- Four browser tests pass at 1440x1000 and 390x844; both light and dark themes.
- Native keyboard range interaction, model-error cases, geometry, stage selection,
  real masks and live threshold calculation verified; no console/network failures.
- axe WCAG A/AA checks report zero violations; direct report refresh and local links pass.
- Rendered hero, quality and real-study views visually inspected. Large scientific
  figures expose full-size links; mobile profile labels render at readable logical sizes.
- Reference URL audit retained in reference-links.json. IEEE bibliographic endpoint
  returns 202; its bibliographic record was independently checked with web search.
- Lighthouse mobile performance 99,
  accessibility/best practices/SEO 100; LCP 1.80s,
  CLS 0.000. This is a lab audit,
  not field Core Web Vitals or an operational SLA. Full local reports are retained.
- Lighthouse desktop performance/accessibility/best practices/SEO 100.

Screenshots are reproducible with `node scripts/capture-ui.cjs` and excluded from
Git to avoid unnecessary binary duplication. Scientific figures, cropped data and
machine-readable results are committed. Public deployment is verified separately
with the same browser suite after Pages publishes; final status is recorded here
when completed. Upstream RTC processing was documented, not independently rerun.
