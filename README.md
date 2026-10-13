# SAR OBSERVATORY
## From Radar Echoes to Earth Intelligence

[Public observatory](https://mohammedumarasif.github.io/sar-observatory/) •
[Research question and sources](docs/research-brief.md) •
[Generated report](docs/report.md) • [Learn the code](docs/learning-plan.md)

A coherent, bounded SAR instrument connecting delayed complex echoes,
backprojection, image-quality gates and a real Sentinel-1 lake study.
It tests whether sharp images can still fail geometric validation and whether
adaptive thresholds support a reliable temporal water-extent comparison.

This is an educational research portfolio developed with Codex assistance.
It is not a full spaceborne processor, flood-confirmation service, novel research
claim or evidence of prior production employment. No Synspective affiliation.

```sh
uv sync --locked
uv run pytest -q
uv run python -m sar_observatory.experiments --no-cache
uv run python scripts/build_site.py
uv run python -m http.server 8080 --directory site
```

Open localhost:8080. Small licensed real crops are bundled, so scientific
reproduction needs no data credentials. See [reproduction instructions](docs/reproducibility.md)
for locked checks, optional COG downloads, browser verification and deployment.
All published numerical results/figures come from committed code. Runtime and RSS
are machine-specific; hashes identify configurations, source modules and artifacts.

Start with [the code map](docs/code-map.md), then [mathematics to code](docs/math-to-code.md),
[pipeline trace](docs/pipeline-walkthrough.md), [failure atlas](docs/failure-atlas.md),
[real products](docs/real-data.md) and [interview guide](docs/interview-guide.md).
Code: MIT. Data: contains modified Copernicus Sentinel data 2019/2020; Catalyst
RTC via Microsoft Planetary Computer (collection CC BY 4.0). See separate attribution.
