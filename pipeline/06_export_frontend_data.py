"""
Script 06 — Export Frontend Data
==================================

INPUT:  data/full_mapped.json       (output of 05_map_full.py)
        data/district_summary.json  (output of 05_map_full.py)
OUTPUT: frontend/public/points.json         — lightweight positions file (x, y, cluster, likes only)
        frontend/public/districts.json      — top-level district metadata for labels + colours
        frontend/public/sub_districts.json  — sub-district centroids + keywords (for zoom-in labels)
        frontend/public/tweets.json         — full tweet text, indexed by id (loaded on demand)

WHY SPLIT THE DATA:
    full_mapped.json is ~300MB — too large to ship to a browser.
    We split it into:

    points.json      — everything needed to DRAW the city (one entry per tweet)
                       x, y, cluster_top, cluster_sub, likes, id
                       ~15MB — loads fast, renders immediately

    districts.json   — top-level district metadata for labels, colours, centroids
                       tiny, loads instantly

    sub_districts.json — sub-level district metadata (61 sub-districts)
                         centroids + keywords, loaded alongside districts.json
                         labels appear when zoomed in past the zoom threshold

    tweets.json      — full text of every tweet, keyed by id
                       loaded lazily when the user clicks a point
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR    = Path(__file__).parent.parent / "data"
PUBLIC_DIR  = Path(__file__).parent.parent / "frontend" / "public"
PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

# Same stopwords as script 05 — keep keyword extraction consistent
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "i", "you", "it", "is", "was", "are", "be", "been",
    "have", "has", "had", "do", "did", "will", "would", "could", "should",
    "that", "this", "they", "we", "he", "she", "my", "your", "its", "our",
    "not", "no", "so", "if", "as", "by", "from", "up", "about", "into",
    "just", "like", "more", "can", "also", "when", "what", "how", "all",
    "there", "their", "them", "than", "then", "some", "out", "get", "got",
    "think", "know", "want", "need", "one", "time", "way", "go", "going",
    "people", "see", "good", "very", "really", "much", "make", "take",
    "said", "say", "even", "still", "back", "well", "too", "something",
    "because", "things", "thing", "feel", "lot", "come", "actually",
    "always", "every", "never", "now", "here", "mean", "right", "made",
    "who", "why", "where", "those", "these", "him", "her", "himself",
    "herself", "over", "after", "before", "between", "through", "during",
    "without", "within", "again", "further", "once", "both", "few", "more",
    "most", "other", "own", "same", "than", "too", "very", "let", "new",
    "first", "last", "long", "great", "little", "work", "old", "life",
    "it's", "i'm", "don't", "can't", "won't", "isn't", "aren't", "wasn't",
    "weren't", "i've", "you've", "we've", "they've", "i'd", "you'd",
    "he'd", "she'd", "we'd", "they'd", "i'll", "you'll", "he'll", "she'll",
    "we'll", "they'll", "that's", "who's", "what's", "here's", "there's",
    "let's", "he's", "she's", "it'd", "yea", "yeah", "etc", "lol", "yes",
    "nah", "hey", "hm", "hmm", "oh", "okay", "ok", "kind", "lot", "bit",
    "https", "http", "com", "www", "t.co",
}


def get_keywords(texts, top_n=6):
    words = []
    for text in texts:
        for w in re.findall(r"[a-zA-Z][a-zA-Z']*[a-zA-Z]", text):
            w_lower = w.lower()
            if w_lower not in STOPWORDS and len(w_lower) >= 3:
                words.append(w_lower)
    return [word for word, _ in Counter(words).most_common(top_n)]


def main():
    print("=" * 60)
    print("Script 06 — Export Frontend Data")
    print("=" * 60)

    # ── Load full mapped data ─────────────────────────────────────────
    print(f"\nLoading full_mapped.json...")
    with open(DATA_DIR / "full_mapped.json", "r", encoding="utf-8") as f:
        tweets = json.load(f)
    print(f"Loaded {len(tweets):,} tweets")

    # ── Compute coordinate normalisation ─────────────────────────────
    xs = [t["x"] for t in tweets]
    ys = [t["y"] for t in tweets]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_range = x_max - x_min
    y_range = y_max - y_min

    # ── points.json — lightweight render data ─────────────────────────
    points = []
    for t in tweets:
        points.append({
            "id":  t["id"],
            "x":   round((t["x"] - x_min) / x_range, 5),
            "y":   round((t["y"] - y_min) / y_range, 5),
            "ct":  t["cluster_top"],   # top-level district
            "cs":  t["cluster_sub"],   # sub-level district
            "l":   t["likes"],         # likes (for landmark sizing)
            "yr":  int(t["date"][:4]), # year (for assembly animation)
        })

    points_path = PUBLIC_DIR / "points.json"
    with open(points_path, "w", encoding="utf-8") as f:
        json.dump(points, f, separators=(",", ":"))  # compact, no spaces
    size_mb = points_path.stat().st_size / 1024 / 1024
    print(f"\npoints.json saved ({size_mb:.1f} MB) — {len(points):,} points")

    # ── districts.json — top-level district metadata ──────────────────
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

    # ── sub_districts.json — sub-level district metadata ─────────────
    # Compute centroids + keywords for each sub-district from tweet data.
    # sub-districts with cs == -1 are standalone (noise) — skip them.
    print(f"\nComputing sub-district centroids and keywords...")
    sub_groups = defaultdict(lambda: {"texts": [], "xs": [], "ys": [], "ct": -1})

    for t in tweets:
        cs = t["cluster_sub"]
        if cs == -1:
            continue
        sub_groups[cs]["texts"].append(t["text"])
        sub_groups[cs]["xs"].append(t["x"])
        sub_groups[cs]["ys"].append(t["y"])
        # Parent top-level district (use mode — most common ct in this sub)
        if sub_groups[cs]["ct"] == -1:
            sub_groups[cs]["ct"] = t["cluster_top"]

    sub_districts = []
    for cs, data in sorted(sub_groups.items()):
        cx_raw = sum(data["xs"]) / len(data["xs"])
        cy_raw = sum(data["ys"]) / len(data["ys"])
        sub_districts.append({
            "id":    cs,
            "ct":    data["ct"],   # parent top-level district
            "count": len(data["texts"]),
            "cx":    round((cx_raw - x_min) / x_range, 5),
            "cy":    round((cy_raw - y_min) / y_range, 5),
            "keywords": get_keywords(data["texts"], top_n=4),
        })

    sub_path = PUBLIC_DIR / "sub_districts.json"
    with open(sub_path, "w", encoding="utf-8") as f:
        json.dump(sub_districts, f, indent=2, ensure_ascii=False)
    print(f"sub_districts.json saved — {len(sub_districts)} sub-districts")

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

    # ── connections.json — reply chain pairs (flat index array) ──────────
    # Each pair [from_idx, to_idx] is stored as two consecutive ints.
    # Indices refer to positions in the points array above.
    print(f"\nLoading full_tweets_meta.json for reply connections...")
    meta_path = DATA_DIR / "full_tweets_meta.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        # Build tweet id → (index, cluster_top, cluster_sub) map
        id_to_data = {t["id"]: (i, t["cluster_top"], t["cluster_sub"])
                      for i, t in enumerate(tweets)}

        # Road type: 2=highway (cross-district), 1=street (same district),
        #            0=alley (same sub-district)
        connections = []  # flat [from_idx, to_idx, type, ...]
        for m in meta:
            rid = m.get("reply_to_id")
            if rid and m["id"] in id_to_data and rid in id_to_data:
                from_idx, from_ct, from_cs = id_to_data[m["id"]]
                to_idx,   to_ct,   to_cs   = id_to_data[rid]
                if from_ct != to_ct:
                    road_type = 2   # highway — cross-district
                elif from_cs != to_cs:
                    road_type = 1   # street — same district, diff sub
                else:
                    road_type = 0   # alley — same sub-district
                connections.extend([from_idx, to_idx, road_type])

        conn_path = PUBLIC_DIR / "connections.json"
        with open(conn_path, "w", encoding="utf-8") as f:
            json.dump(connections, f, separators=(",", ":"))
        size_mb = conn_path.stat().st_size / 1024 / 1024
        n = len(connections) // 3
        hw = sum(1 for i in range(n) if connections[i*3+2] == 2)
        st = sum(1 for i in range(n) if connections[i*3+2] == 1)
        al = sum(1 for i in range(n) if connections[i*3+2] == 0)
        print(f"connections.json saved ({size_mb:.1f} MB) — {n:,} connections "
              f"({hw:,} highways · {st:,} streets · {al:,} alleys)")
    else:
        print("full_tweets_meta.json not found — skipping connections export")

    print(f"\nAll frontend data exported to: {PUBLIC_DIR}")

if __name__ == "__main__":
    main()
