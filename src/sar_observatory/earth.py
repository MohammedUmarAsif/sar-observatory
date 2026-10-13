"""Real Sentinel-1 RTC crops: unsigned provenance, common grid, water candidates."""

import argparse
import json

import numpy as np
import rasterio
import requests
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform
from rasterio.windows import from_bounds

from .pipeline import ROOT, checksum, log, write_json

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
# Covers a lake-margin mosaic rather than the entire Poyang Lake.
AOI_CENTER = (116.17, 29.10)
SIZE = 1024
PIXEL_M = 10.0


def get_json(url, params=None):
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def fetch():
    """Two fixed-geometry date searches; pin chosen STAC records after first fetch."""
    source_dir = ROOT / "data" / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    collection = get_json(f"{STAC}/collections/sentinel-1-rtc")
    write_json(source_dir / "collection.json", collection)
    cx, cy = transform("EPSG:4326", "EPSG:32650", [AOI_CENTER[0]], [AOI_CENTER[1]])
    # One common integer-metre grid. Source grids may have different origins.
    xmin = round(cx[0] / 10) * 10 - SIZE * PIXEL_M / 2
    ymax = round(cy[0] / 10) * 10 + SIZE * PIXEL_M / 2
    grid = from_origin(xmin, ymax, PIXEL_M, PIXEL_M)
    bounds = (xmin, ymax - SIZE * PIXEL_M, xmin + SIZE * PIXEL_M, ymax)
    for name, interval in [
        ("before", "2019-12-01T00:00:00Z/2019-12-31T23:59:59Z"),
        ("after", "2020-07-01T00:00:00Z/2020-07-31T23:59:59Z"),
    ]:
        destination = ROOT / "data" / f"{name}.tif"
        record_path = source_dir / f"{name}.json"
        if destination.exists() and record_path.exists():
            log("earth_fetch", period=name, action="reuse bundled crop")
            continue
        if record_path.exists():
            item = json.loads(record_path.read_text(encoding="utf-8"))
        else:
            lon, lat = AOI_CENTER
            items = get_json(
                f"{STAC}/search",
                {
                    "collections": "sentinel-1-rtc",
                    "bbox": f"{lon - 0.01},{lat - 0.01},{lon + 0.01},{lat + 0.01}",
                    "datetime": interval,
                    "limit": 100,
                },
            )["features"]
            candidates = [
                i
                for i in items
                if i["properties"]["platform"] == "SENTINEL-1A"
                and i["properties"]["sat:relative_orbit"] == 40
                and i["properties"]["sat:orbit_state"] == "ascending"
            ]
            if not candidates:
                raise ValueError(f"no same-platform orbit-40 acquisitions for {name}")
            item = sorted(candidates, key=lambda i: i["properties"]["datetime"])[0]
            write_json(record_path, item)
        href = item["assets"]["vv"]["href"]
        account = href.split("/")[2].split(".")[0]
        container = href.split("/")[3]
        # Do not persist or log the ephemeral access token.
        token = get_json(
            f"https://planetarycomputer.microsoft.com/api/sas/v1/token/{account}/{container}"
        )["token"]
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_TIMEOUT="60"):  # noqa: SIM117 - environment must surround dataset lifetime
            with rasterio.open(href + "?" + token) as source:
                if source.crs != rasterio.crs.CRS.from_epsg(32650):
                    raise ValueError("selected source has unexpected CRS")
                window = (
                    from_bounds(*bounds, transform=source.transform).round_offsets().round_lengths()
                )
                if (
                    window.col_off < 0
                    or window.row_off < 0
                    or window.col_off + window.width > source.width
                    or window.row_off + window.height > source.height
                ):
                    raise ValueError("crop is not fully contained in source acquisition")
                values = source.read(1, window=window)
                dest = np.full((SIZE, SIZE), -32768.0, dtype="float32")
                reproject(
                    values,
                    dest,
                    src_transform=source.window_transform(window),
                    src_crs=source.crs,
                    src_nodata=source.nodata,
                    dst_transform=grid,
                    dst_crs="EPSG:32650",
                    dst_nodata=-32768.0,
                    resampling=Resampling.bilinear,
                )
                with rasterio.open(
                    destination,
                    "w",
                    driver="GTiff",
                    height=SIZE,
                    width=SIZE,
                    count=1,
                    dtype="float32",
                    crs="EPSG:32650",
                    transform=grid,
                    nodata=-32768.0,
                    compress="deflate",
                ) as output:
                    output.write(dest, 1)
                    output.update_tags(
                        units="linear gamma0 power",
                        source_item=item["id"],
                        attribution=(
                            "Contains modified Copernicus Sentinel data; "
                            "Catalyst RTC via Microsoft Planetary Computer"
                        ),
                    )
        log("earth_fetch", period=name, id=item["id"], sha256=checksum(destination))


def otsu_threshold(values, bins=256):
    """Maximize between-class variance in dB, fixed histogram range [-40,5]."""
    values = np.asarray(values)
    if not np.isfinite(values).all() or values.size < 16:
        raise ValueError("Otsu requires >=16 finite valid dB samples")
    hist, edges = np.histogram(values, bins=bins, range=(-40, 5))
    if hist.sum() == 0 or np.count_nonzero(hist) < 2:
        raise ValueError("no separable histogram in supported [-40,5] dB window")
    centers = (edges[1:] + edges[:-1]) / 2
    weight = np.cumsum(hist) / hist.sum()
    means = np.cumsum(hist * centers) / hist.sum()
    denom = weight * (1 - weight)
    score = np.divide(
        (means[-1] * weight - means) ** 2, denom, out=np.zeros_like(weight), where=denom > 0
    )
    return float(edges[int(np.argmax(score)) + 1])


def load_pair():
    arrays, records, transforms = [], [], []
    for name in ("before", "after"):
        with rasterio.open(ROOT / "data" / f"{name}.tif") as source:
            arrays.append(source.read(1))
            transforms.append((source.crs, source.transform, source.shape))
        records.append(
            json.loads((ROOT / "data" / "source" / f"{name}.json").read_text(encoding="utf-8"))
        )
    if transforms[0] != transforms[1]:
        raise ValueError("real intensity comparison requires identical CRS/transform/shape")
    valid = np.isfinite(arrays[0]) & np.isfinite(arrays[1]) & (arrays[0] > 0) & (arrays[1] > 0)
    if valid.mean() < 0.9:
        raise ValueError("common valid coverage below 90%; select another crop")
    db = [10 * np.log10(np.where(valid, a, 1)) for a in arrays]
    return db, valid, records, transforms[0][1]


def block_change_interval(before, after, valid, block=128, seed=17):
    """Paired spatial-block resampling; descriptive heterogeneity, not accuracy CI."""
    sums, counts = [], []
    change = after.astype(float) - before.astype(float)
    for row in range(0, valid.shape[0], block):
        for col in range(0, valid.shape[1], block):
            region = np.s_[row : row + block, col : col + block]
            counts.append(int(valid[region].sum()))
            sums.append(float(change[region][valid[region]].sum()))
    counts, sums = np.asarray(counts), np.asarray(sums)
    keep = counts > 0
    counts, sums = counts[keep], sums[keep]
    draws = np.random.default_rng(seed).integers(0, len(counts), size=(1000, len(counts)))
    distribution = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
    return {
        "block_pixels": block,
        "block_m": block * PIXEL_M,
        "blocks": len(counts),
        "replicates": 1000,
        "change_fraction_interval_95": np.quantile(distribution, [0.025, 0.975]).tolist(),
    }


def analyze():
    db, valid, records, grid = load_pair()
    thresholds = [otsu_threshold(d[valid]) for d in db]
    results = {}
    masks = {}
    for method, levels in [("fixed", [-17.0, -17.0]), ("otsu", thresholds)]:
        water = [(d < level) & valid for d, level in zip(db, levels, strict=True)]
        fractions = [float(m.sum() / valid.sum()) for m in water]
        results[method] = {
            "threshold_db": levels,
            "fraction": fractions,
            "candidate_area_km2": [float(m.sum() * PIXEL_M**2 / 1e6) for m in water],
            "change_fraction": fractions[1] - fractions[0],
            "blocks": [
                block_change_interval(water[0], water[1], valid, block=b) for b in (64, 128, 256)
            ],
        }
        masks[method] = water
    output = {
        "schema": 1,
        "interpretation": "candidate open-water extent, not confirmed flooding",
        "reference_labels": "none; no accuracy or flood confirmation claimed",
        "aoi_center_lon_lat": AOI_CENTER,
        "crs": "EPSG:32650",
        "pixel_m": PIXEL_M,
        "shape": list(valid.shape),
        "valid_fraction": float(valid.mean()),
        "transform": list(grid)[:6],
        "methods": results,
        "threshold_sensitivity": {
            str(t): [float(((d < t) & valid).sum() / valid.sum()) for d in db]
            for t in (-19, -18, -17, -16, -15)
        },
        "method_disagreement_fraction": [
            float(np.mean(masks["fixed"][i][valid] != masks["otsu"][i][valid])) for i in (0, 1)
        ],
        "acquisitions": [
            {"id": r["id"], "properties": r["properties"], "asset": r["assets"]["vv"]}
            for r in records
        ],
        "data_sha256": {
            f"{n}.tif": checksum(ROOT / "data" / f"{n}.tif") for n in ("before", "after")
        },
        "rasterio": rasterio.__version__,
        "gdal": rasterio.__gdal_version__,
    }
    write_json(ROOT / "results" / "earth.json", output)
    return output, db, valid, masks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="download pinned COG windows")
    args = parser.parse_args()
    if args.fetch:
        fetch()
    result, *_ = analyze()
    print(json.dumps(result["methods"], indent=2))
