# SAR Observatory

Use uv, Ruff, ty, pytest. Read docs/visual-contract.md before UI edits.
Keep units, complex phase, sampling assumptions, measurement definitions and provenance explicit.
Regenerate scientific artifacts with `uv run python -m sar_observatory.experiments`.
Real data must remain separately labeled. Never infer coherence from detected intensity.
Run scientific tests and verify desktop/mobile UI before publishing. No invented results.
