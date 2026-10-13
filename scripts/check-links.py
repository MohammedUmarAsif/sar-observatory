"""Bounded primary-reference link audit; records response, never invents availability."""

import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]


def check(url):
    try:
        with requests.get(url, timeout=30, stream=True) as response:
            return {"url": url, "status": response.status_code}
    except requests.RequestException as exc:
        return {"url": url, "error": type(exc).__name__}


if __name__ == "__main__":
    import json

    urls = sorted(
        set(
            re.findall(
                r"https://[^)\s]+",
                (ROOT / "docs" / "research-brief.md").read_text(encoding="utf-8"),
            )
        )
    )
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(check, urls))
    (ROOT / "verification" / "reference-links.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, indent=2))
