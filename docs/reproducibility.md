# Reproduce the observatory

Requires Python 3.12 and uv; Node 22+ is needed only for browser verification.
No credentials or Python server are required by the public website. Bundled
licensed real-data crops allow the default full scientific demo to run offline
after dependencies are installed. The entire source archive is available on GitHub.

```sh
git clone https://github.com/MohammedUmarAsif/sar-observatory.git
cd sar-observatory
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run ty check src
uv run python -m sar_observatory.experiments --no-cache
uv run python scripts/build_site.py
```

Serve locally for inspection (fetch cannot load artifacts from a file:// page):

```sh
uv run python -m http.server 8080 --directory site
```

Open `http://localhost:8080`. The deployed repository path is
`https://mohammedumarasif.github.io/sar-observatory/`. Assets use relative paths
and section links use hashes. Generated notes are plain HTML and refresh directly.

## Download workflow

```sh
uv run python -m sar_observatory.earth --fetch
```

If bundled TIFFs already exist, this preserves them. To redownload into a fresh
clone, first move the two crop files to a backup location while retaining pinned
`data/source/before.json` and `after.json`; then run the fetch command. The code
requests ephemeral signed URLs from Planetary Computer, reads only bounded COG
windows and never stores access tokens. Anonymous access succeeded during this
build, but the provider documents account requirements and can change access.
On denial, retain the bundled credential-free path and report the actual error.
No multi-GB full acquisition is required. Approximate crop storage is 8 MB; COG
window transfer may exceed that due to underlying tile compression and requests.
Do not fetch or redistribute full proprietary/non-licensed datasets.

## Numerical and artifact provenance

`configs/demo.json` fixes acquisition parameters; each experiment changes one
factor. Seeds are 17 for the main cases and 101-106 for noise repetitions.
`uv.lock` pins packages; manifests include its hash and per-module SHA-256.
`results/synthetic.json` contains scientific measurements and machine-specific
runtime/RSS; `results/earth.json` contains acquisition metadata and crop hashes.
`results/inventory.json` records SHA-256 for numerical artifacts, source records,
licensed crops and published figures. Source file hashes are authoritative even
while a generating change has not yet been committed. No secrets appear in artifacts.

Complex stage arrays are cached under `artifacts/cache` and deliberately excluded
from Git. Rerunning without `--no-cache` validates and reuses them. Images and
tables regenerate from code. Runtime/RSS change across reruns and hardware; these
are not bitwise reproducible performance results. Scientific values should be
stable under the locked environment; FFT/library/platform variation may cause
small floating-point differences. Raster reprocessing versions can change crop
bytes, so published bundled crops define the reference numerical dataset.

## Browser checks

```sh
npm ci
npx playwright install chromium
npm test
```

The suite starts a local static server, checks desktop/mobile overflow, interactions,
direct note links, broken images, console/network failures and axe accessibility.
`verification/` contains a committed verification summary; local screenshots are
excluded from Git. A public URL can be checked with
`SAR_BASE_URL=https://mohammedumarasif.github.io/sar-observatory/ npm test` on POSIX,
or `$env:SAR_BASE_URL='https://mohammedumarasif.github.io/sar-observatory/'; npm test`
in PowerShell. GitHub Actions checks the science and deploys the checked static site.

## Licences and authorship

Code is MIT licensed. Crop/data attribution is separate: contains modified
Copernicus Sentinel data 2019 and 2020; Catalyst RTC via Planetary Computer,
collection CC-BY-4.0. Primary references are linked in the research brief.
Codex assistance is documented in AUTHORS.md. No employer affiliation or guarantee
of employment is implied. Every scientific claim is limited to its implemented model,
selected real crop and actual evidence.
