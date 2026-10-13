"""Render project notes into serverless HTML with relative assets and links."""

import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
notes = ROOT / "site" / "notes"
notes.mkdir(parents=True, exist_ok=True)
for source in sorted((ROOT / "docs").glob("*.md")):
    text = source.read_text(encoding="utf-8")
    text = re.sub(r"\]\(([^:)]+)\.md\)", r"](\1.html)", text)
    rendered = markdown.markdown(text, extensions=["tables", "fenced_code"])
    title = text.splitlines()[0].removeprefix("# ")
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | SAR Observatory</title>
<link rel="stylesheet" href="../style.css"><link rel="icon" href="../favicon.svg"></head><body>
<header class="nav"><a class="brand" href="../index.html">SAR OBSERVATORY</a>
<nav aria-label="Documentation navigation"><a href="../index.html#laboratory">Laboratory</a>
<a href="code-map.html">Code map</a><a href="learning-plan.html">Learn</a>
<a href="https://github.com/MohammedUmarAsif/sar-observatory">Source ↗</a></nav></header>
<main class="wrap document"><a class="back-link" href="../index.html">← Back to the observatory</a>
{rendered}</main><footer class="wrap">
<p>Educational research portfolio developed with Codex assistance.</p>
<a href="https://github.com/MohammedUmarAsif/sar-observatory/blob/main/docs/{source.name}">
Read this source on GitHub ↗</a></footer>
</body></html>"""
    (notes / f"{source.stem}.html").write_text(html, encoding="utf-8", newline="\n")
print(f"Built {len(list(notes.glob('*.html')))} static research notes.")
