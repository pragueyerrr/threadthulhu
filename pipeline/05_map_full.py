"""
Script 05 — Map the Full Archive: UMAP + HDBSCAN (Two-level hierarchy)
=======================================================================

INPUT:  data/full_embeddings.npy     (output of 04_embed_full.py)
        data/full_tweets_meta.json   (output of 04_embed_full.py)
OUTPUT: data/full_mapped.json        — all tweets with x/y coords + cluster_top + cluster_sub
        data/full_map.png            — scatter plot coloured by top-level districts
        data/district_summary.json   — per-district stats for both levels

TWO-LEVEL HIERARCHY:
    The city has two zoom levels, each produced by a separate HDBSCAN pass
    on the same cached 15D UMAP space:

    TOP LEVEL  (cluster_top)  — 20-30 named districts, visible when zoomed out
                                HDBSCAN_MIN_CLUSTER_SIZE_TOP = 750
    SUB LEVEL  (cluster_sub)  — 60+ sub-districts, visible when zoomed in
                                HDBSCAN_MIN_CLUSTER_SIZE_SUB = 300

    Each tweet gets both IDs. The frontend switches between them based on zoom.
    This mirrors how real cities work: borough → neighbourhood → street.

TUNING GUIDE:
    Too few top districts (< 15):  lower  HDBSCAN_MIN_CLUSTER_SIZE_TOP (try 500)
    Too many top districts (> 35): raise  HDBSCAN_MIN_CLUSTER_SIZE_TOP (try 1000)
    Districts feel random:         raise  UMAP_CLUSTER_N_NEIGHBORS (try 50)
"""

import json
import re
import numpy as np
from pathlib import Path
from collections import Counter
from datetime import datetime


class NumpyEncoder(json.JSONEncoder):
    """Handles numpy int64/float32/etc that json.dump chokes on."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

# ─── Configuration ────────────────────────────────────────────────────────────

DATA_DIR      = Path(__file__).parent.parent / "data"
INPUT_EMBS    = DATA_DIR / "full_embeddings.npy"
INPUT_META    = DATA_DIR / "full_tweets_meta.json"
OUTPUT_MAP    = DATA_DIR / "full_mapped.json"
OUTPUT_PLOT   = DATA_DIR / "full_map.png"
OUTPUT_SUMMARY = DATA_DIR / "district_summary.json"

# Stage 1: UMAP for clustering
UMAP_CLUSTER_N_COMPONENTS = 15
UMAP_CLUSTER_N_NEIGHBORS  = 30
UMAP_CLUSTER_MIN_DIST     = 0.0

# Stage 2: UMAP for 2D visualisation
UMAP_VIZ_N_COMPONENTS = 2
UMAP_VIZ_N_NEIGHBORS  = 15
UMAP_VIZ_MIN_DIST     = 0.1

# HDBSCAN — two passes, two zoom levels
HDBSCAN_MIN_CLUSTER_SIZE_TOP = 750   # top-level: ~20-30 named districts
HDBSCAN_MIN_CLUSTER_SIZE_SUB = 300   # sub-level: ~61 sub-districts
HDBSCAN_MIN_SAMPLES          = 10

KEYWORDS_PER_CLUSTER = 15
EXAMPLES_PER_CLUSTER = 3

# ─── Helpers ──────────────────────────────────────────────────────────────────

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
    # contractions — explicitly listed to catch the whole word
    "it's", "i'm", "don't", "can't", "won't", "isn't", "aren't", "wasn't",
    "weren't", "i've", "you've", "we've", "they've", "i'd", "you'd",
    "he'd", "she'd", "we'd", "they'd", "i'll", "you'll", "he'll", "she'll",
    "we'll", "they'll", "that's", "who's", "what's", "here's", "there's",
    "let's", "he's", "she's", "it'd", "yea", "yeah", "etc", "lol", "yes",
    "nah", "hey", "hm", "hmm", "oh", "okay", "ok", "kind", "lot", "bit",
    # urls — these are noise, not topics
    "https", "http", "com", "www", "t.co",
}


def get_keywords(texts, top_n=KEYWORDS_PER_CLUSTER):
    """Extract meaningful keywords from a set of tweet texts."""
    words = []
    for text in texts:
        # Match whole words including contractions
        for w in re.findall(r"[a-zA-Z][a-zA-Z']*[a-zA-Z]", text):
            w_lower = w.lower()
            if w_lower not in STOPWORDS and len(w_lower) >= 3:
                words.append(w_lower)
    return [word for word, _ in Counter(words).most_common(top_n)]


def date_to_year(date_str):
    return int(date_str[:4])


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    import umap
    import hdbscan
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm

    print("=" * 60)
    print("Script 05 — Map Full Archive (Two-stage UMAP + HDBSCAN)")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")

    # ── Load ─────────────────────────────────────────────────────────
    print(f"\nLoading embeddings: {INPUT_EMBS}")
    embeddings = np.load(INPUT_EMBS)
    print(f"Embeddings shape: {embeddings.shape}")

    print(f"Loading metadata: {INPUT_META}")
    with open(INPUT_META, "r", encoding="utf-8") as f:
        tweets = json.load(f)
    print(f"Tweets: {len(tweets):,}")

    assert len(embeddings) == len(tweets), "Mismatch between embeddings and metadata!"

    # ── Stage 1: UMAP 768D → 15D ─────────────────────────────────────
    cache_15d = DATA_DIR / "_umap_15d.npy"
    if cache_15d.exists():
        print(f"\n[Stage 1] Loading cached 15D UMAP from: {cache_15d.name}")
        embedding_15d = np.load(cache_15d)
        print(f"  Shape: {embedding_15d.shape}")
    else:
        print(f"\n[Stage 1] UMAP → {UMAP_CLUSTER_N_COMPONENTS}D for clustering...")
        print(f"  n_neighbors={UMAP_CLUSTER_N_NEIGHBORS}, min_dist={UMAP_CLUSTER_MIN_DIST}")
        print("  (This is the slow step — 10-20 min for 247k tweets)")
        reducer_cluster = umap.UMAP(
            n_components=UMAP_CLUSTER_N_COMPONENTS,
            n_neighbors=UMAP_CLUSTER_N_NEIGHBORS,
            min_dist=UMAP_CLUSTER_MIN_DIST,
            metric="cosine",
            random_state=42,
            low_memory=False,
            verbose=True,
        )
        embedding_15d = reducer_cluster.fit_transform(embeddings)
        print(f"  Done at {datetime.now().strftime('%H:%M:%S')}")
        np.save(cache_15d, embedding_15d)
        print(f"  15D embedding saved to: {cache_15d.name}")

    # ── HDBSCAN — top level (~20-30 districts) ───────────────────────
    print(f"\n[Stage 1] HDBSCAN — top level (min_cluster_size={HDBSCAN_MIN_CLUSTER_SIZE_TOP})...")
    clusterer_top = hdbscan.HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE_TOP,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        core_dist_n_jobs=-1,
    )
    labels_top = clusterer_top.fit_predict(embedding_15d)

    top_ids    = sorted(set(labels_top))
    n_top      = len([l for l in top_ids if l != -1])
    n_noise_top = sum(1 for l in labels_top if l == -1)
    print(f"  Top-level districts: {n_top}")
    print(f"  Standalone/noise:    {n_noise_top:,} ({100*n_noise_top/len(labels_top):.1f}%)")

    # ── HDBSCAN — sub level (~61 districts) ──────────────────────────
    print(f"\n[Stage 1] HDBSCAN — sub level (min_cluster_size={HDBSCAN_MIN_CLUSTER_SIZE_SUB})...")
    clusterer_sub = hdbscan.HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE_SUB,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
        core_dist_n_jobs=-1,
    )
    labels_sub = clusterer_sub.fit_predict(embedding_15d)

    sub_ids     = sorted(set(labels_sub))
    n_sub       = len([l for l in sub_ids if l != -1])
    n_noise_sub = sum(1 for l in labels_sub if l == -1)
    print(f"  Sub-level districts: {n_sub}")
    print(f"  Standalone/noise:    {n_noise_sub:,} ({100*n_noise_sub/len(labels_sub):.1f}%)")

    # Use top-level for the main plot and summaries
    labels      = labels_top
    cluster_ids = top_ids
    n_clusters  = n_top
    n_noise     = n_noise_top

    # ── Stage 2: UMAP 768D → 2D for visualisation ────────────────────
    print(f"\n[Stage 2] UMAP → 2D for city layout...")
    reducer_viz = umap.UMAP(
        n_components=UMAP_VIZ_N_COMPONENTS,
        n_neighbors=UMAP_VIZ_N_NEIGHBORS,
        min_dist=UMAP_VIZ_MIN_DIST,
        metric="cosine",
        random_state=42,
        low_memory=False,
        verbose=True,
    )
    coords = reducer_viz.fit_transform(embeddings)
    print(f"  Done at {datetime.now().strftime('%H:%M:%S')}")

    # ── District summaries ────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("DISTRICT SUMMARIES")
    print(f"{'=' * 60}")

    district_summary = []
    labels_arr = np.array(labels)

    for cluster_id in cluster_ids:
        if cluster_id == -1:
            continue

        mask           = labels_arr == cluster_id
        cluster_tweets = [t for t, l in zip(tweets, labels) if l == cluster_id]
        texts          = [t["text"] for t in cluster_tweets]
        keywords       = get_keywords(texts)
        likes_list     = [t["likes"] for t in cluster_tweets]
        avg_likes      = sum(likes_list) / len(likes_list)
        max_likes      = max(likes_list)
        years          = [date_to_year(t["date"]) for t in cluster_tweets]
        year_range     = f"{min(years)}–{max(years)}"
        top_tweets     = sorted(cluster_tweets, key=lambda t: t["likes"], reverse=True)

        print(f"\n{'─' * 55}")
        print(f"District {cluster_id}  ·  {len(cluster_tweets):,} tweets  ·  avg {avg_likes:.0f} likes  ·  {year_range}")
        print(f"Keywords: {', '.join(keywords[:10])}")
        for tweet in top_tweets[:EXAMPLES_PER_CLUSTER]:
            preview = tweet["text"][:140].replace("\n", " ")
            print(f"  [{tweet['likes']:,} ♥] {preview}...")

        district_summary.append({
            "id":          cluster_id,
            "tweet_count": int(mask.sum()),
            "avg_likes":   round(avg_likes, 1),
            "max_likes":   int(max_likes),
            "year_range":  year_range,
            "keywords":    keywords,
            "top_tweet":   top_tweets[0]["text"] if top_tweets else "",
            "centroid_x":  float(coords[mask, 0].mean()),
            "centroid_y":  float(coords[mask, 1].mean()),
        })

    # ── Save district summary ─────────────────────────────────────────
    with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(district_summary, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
    print(f"\nDistrict summary saved to: {OUTPUT_SUMMARY}")

    # ── Save full mapped data ─────────────────────────────────────────
    print("\nSaving full mapped data (this may take a moment)...")
    result = []
    for i, tweet in enumerate(tweets):
        result.append({
            "id":          tweet["id"],
            "text":        tweet["text"],
            "date":        tweet["date"],
            "likes":       tweet["likes"],
            "x":           float(coords[i, 0]),
            "y":           float(coords[i, 1]),
            "cluster_top": int(labels_top[i]),   # zoomed-out district
            "cluster_sub": int(labels_sub[i]),   # zoomed-in sub-district
        })

    with open(OUTPUT_MAP, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, cls=NumpyEncoder)
    size_mb = OUTPUT_MAP.stat().st_size / 1024 / 1024
    print(f"Full mapped data saved to: {OUTPUT_MAP}  ({size_mb:.0f} MB)")

    # ── Scatter plot ──────────────────────────────────────────────────
    print("\nGenerating city map visualisation...")

    fig, ax = plt.subplots(figsize=(18, 12))
    fig.patch.set_facecolor("#0d0d0d")
    ax.set_facecolor("#0d0d0d")

    colors    = cm.tab20(np.linspace(0, 1, max(n_clusters, 1)))
    labels_np = np.array(labels)

    # Noise in dim grey
    noise_mask = labels_np == -1
    if noise_mask.any():
        ax.scatter(
            coords[noise_mask, 0], coords[noise_mask, 1],
            c="#222222", s=0.5, alpha=0.3,
        )

    # Districts
    for i, cluster_id in enumerate([l for l in cluster_ids if l != -1]):
        mask   = labels_np == cluster_id
        d      = next(d for d in district_summary if d["id"] == cluster_id)
        kw     = d["keywords"][:2]
        label  = f"D{cluster_id}: {' · '.join(kw)} ({mask.sum():,})"
        ax.scatter(
            coords[mask, 0], coords[mask, 1],
            c=[colors[i % 20]], s=1.5, alpha=0.6, label=label,
        )

    ax.set_title(
        f"Threadthulhu City — Full Archive\n({len(tweets):,} tweets · {n_clusters} districts · Two-stage UMAP + HDBSCAN)",
        color="white", fontsize=13, pad=12,
    )
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.legend(
        bbox_to_anchor=(1.02, 1), loc="upper left",
        fontsize=6, framealpha=0.2, labelcolor="white",
        facecolor="#1a1a1a", markerscale=3,
    )

    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Map saved to: {OUTPUT_PLOT}")

    print(f"\nFinished: {datetime.now().strftime('%H:%M:%S')}")
    print(f"\n{'=' * 60}")
    print(f"RESULTS: {n_clusters} districts, {n_noise:,} standalones ({100*n_noise/len(labels):.1f}%)")
    print(f"{'=' * 60}")
    print("\nAiming for 15-40 coherent districts with <40% noise.")
    print("If outside that range, see tuning guide at top of this file.")
    print("\nIf happy with clustering → next step: build the Pixi.js frontend.")

    plt.show()


if __name__ == "__main__":
    main()
