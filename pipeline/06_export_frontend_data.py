"""
Script 06 — Export Frontend Data
==================================

INPUT:  data/full_mapped.json       (output of 05_map_full.py)
        data/district_summary.json  (output of 05_map_full.py)
OUTPUT: frontend/public/points.json     — lightweight positions file (x, y, cluster, likes only)
        frontend/public/districts.json  — district metadata for labels + colours
        frontend/public/tweets.json     — full tweet text, indexed by id (loaded on demand)

WHY SPLIT THE DATA:
    full_mapped.json is ~300MB — too large to ship to a browser.
    We split it into:

    points.json  — everything needed to DRAW the city (one entry per tweet)
                   x, y, cluster_top, cluster_sub, likes, id
                   ~15MB — loads fast, renders immediately

    districts.json — district metadata for labels, colours, centroids
                     tiny, loads instantly

    tweets.json  — full text of every tweet, keyed by id
                   loaded lazily when the user clicks/hovers a point
                   (or chunked by district in a later optimisation)
"""

import json
from pathlib import Path

DATA_DIR    = Path(__file__).parent.parent / "data"
PUBLIC_DIR  = Path(__file__).parent.parent / "frontend" / "public"
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("=" * 60)
    print("Script 06 — Export Frontend Data")
    print("=" * 60)

    # ── Load full mapped data ─────────────────────────────────────────
    print(f"\nLoading full_mapped.json...")
    with open(DATA_DIR / "full_mapped.json", "r", encoding="utf-8") as f:
        tweets = json.load(f)
    print(f"Loaded {len(tweets):,} tweets")

    # ── points.json — lightweight render data ─────────────────────────
    # Normalise x/y to 0-1 range so the frontend doesn't need to know
    # the raw UMAP coordinate space
    xs = [t["x"] for t in tweets]
    ys = [t["y"] for t in tweets]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_range = x_max - x_min
    y_range = y_max - y_min

    points = []
    for t in tweets:
        points.append({
            "id":  t["id"],
            "x":   round((t["x"] - x_min) / x_range, 5),
            "y":   round((t["y"] - y_min) / y_range, 5),
            "ct":  t["cluster_top"],   # top-level district
            "cs":  t["cluster_sub"],   # sub-level district
            "l":   t["likes"],         # likes (for landmark sizing)
        })

    points_path = PUBLIC_DIR / "points.json"
    with open(points_path, "w", encoding="utf-8") as f:
        json.dump(points, f, separators=(",", ":"))  # compact, no spaces
    size_mb = points_path.stat().st_size / 1024 / 1024
    print(f"\npoints.json saved ({size_mb:.1f} MB) — {len(points):,} points")

    # ── districts.json — district metadata ───────────────────────────
    print(f"\nLoading district_summary.json...")
    with open(DATA_DIR / "district_summary.json", "r", encoding="utf-8") as f:
        summary = json.load(f)

    # Normalise centroids to 0-1 range
    for d in summary:
        d["cx"] = round((d["centroid_x"] - x_min) / x_range, 5)
        d["cy"] = round((d["centroid_y"] - y_min) / y_range, 5)
        del d["centroid_x"]
        del d["centroid_y"]

    districts_path = PUBLIC_DIR / "districts.json"
    with open(districts_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"districts.json saved — {len(summary)} districts")

    # ── tweets.json — full text indexed by id ────────────────────────
    tweet_text = {
        t["id"]: {
            "text":  t["text"],
            "date":  t["date"],
            "likes": t["likes"],
        }
        for t in tweets
    }

    tweets_path = PUBLIC_DIR / "tweets.json"
    with open(tweets_path, "w", encoding="utf-8") as f:
        json.dump(tweet_text, f, separators=(",", ":"), ensure_ascii=False)
    size_mb = tweets_path.stat().st_size / 1024 / 1024
    print(f"tweets.json saved ({size_mb:.1f} MB)")

    print(f"\nAll frontend data exported to: {PUBLIC_DIR}")
    print("\nNext step: build the Pixi.js city renderer")

if __name__ == "__main__":
    main()
