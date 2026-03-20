"""
Script 03 — Map the Sample: UMAP + HDBSCAN + Visualise
========================================================
v2 — Two-stage UMAP (cluster in 15D, visualise in 2D)

INPUT:  data/sample_embeddings.npy  (output of 02_embed_sample.py)
        data/sample_tweets.json     (output of 02_embed_sample.py)
OUTPUT: data/sample_mapped.json     — tweets with x/y coords and cluster ID
        data/sample_map.png         — scatter plot visualisation

WHAT THIS DOES:
    Takes the 768-dimensional embedding vectors and maps them into a city layout.
    Produces a scatter plot and neighbourhood summaries so we can answer:
    "What are the actual districts of Threadthulhu City?"

TWO-STAGE APPROACH (v2 fix):
    v1 ran HDBSCAN directly on 2D UMAP output. Problem: 2D UMAP compresses
    so aggressively that most points end up in one giant blob — HDBSCAN sees
    one density mass and returns one cluster.

    The standard fix (borrowed from single-cell biology, where this exact
    problem is well-studied) is to separate the two jobs:

      Stage 1 — Cluster in 15D UMAP space:
        UMAP 768D → 15D preserves much more structure than 768D → 2D.
        HDBSCAN on 15D finds genuine semantic clusters (neighbourhoods).

      Stage 2 — Visualise in 2D UMAP space:
        A separate UMAP 768D → 2D produces the city layout for the scatter
        plot. Points are coloured by the clusters found in stage 1.

    This way clustering quality is not sacrificed for visual layout.

THE ALGORITHMS:

    UMAP (Uniform Manifold Approximation and Projection):
        Reduces dimensions while preserving local + global structure.
        n_neighbors: larger = more global, smaller = more local.
        min_dist: smaller = tighter clusters.

    HDBSCAN (Hierarchical Density-Based Spatial Clustering):
        Finds natural density-based clusters without pre-specifying count.
        Labels outliers as noise (-1) — these are standalone buildings / hidden alleys.
        min_cluster_size: raise to merge small clusters, lower to split them.
"""

import json
import re
import numpy as np
from pathlib import Path
from collections import Counter

# ─── Configuration ────────────────────────────────────────────────────────────

DATA_DIR    = Path(__file__).parent.parent / "data"
INPUT_EMBS  = DATA_DIR / "sample_embeddings.npy"
INPUT_META  = DATA_DIR / "sample_tweets.json"
OUTPUT_MAP  = DATA_DIR / "sample_mapped.json"
OUTPUT_PLOT = DATA_DIR / "sample_map.png"

# Stage 1: UMAP for clustering (higher dimensions = better cluster separation)
UMAP_CLUSTER_N_COMPONENTS = 15
UMAP_CLUSTER_N_NEIGHBORS  = 30   # higher = more global structure captured
UMAP_CLUSTER_MIN_DIST     = 0.0  # 0 = pack tightly for clustering (not visualisation)

# Stage 2: UMAP for 2D visualisation layout
UMAP_VIZ_N_COMPONENTS = 2
UMAP_VIZ_N_NEIGHBORS  = 15
UMAP_VIZ_MIN_DIST     = 0.1

# HDBSCAN — run on 15D cluster space
# Lower min_cluster_size = more, smaller districts
# Raise it = fewer, larger districts
HDBSCAN_MIN_CLUSTER_SIZE = 15
HDBSCAN_MIN_SAMPLES      = 5

KEYWORDS_PER_CLUSTER = 12
EXAMPLES_PER_CLUSTER = 2

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
    "t", "re", "s", "don", "ve", "ll", "m", "rt", "http", "https",
    "amp", "said", "say", "even", "still", "back", "well", "too",
    "something", "because", "things", "thing", "feel", "lot", "come",
    "actually", "always", "every", "never", "now", "here", "mean",
    "right", "made", "its", "who", "why", "where", "those", "these",
    "been", "had", "has", "him", "her", "himself", "herself",
}


def get_keywords(texts, top_n=KEYWORDS_PER_CLUSTER):
    words = []
    for text in texts:
        words.extend(
            w.lower()
            for w in re.findall(r"[a-zA-Z']{3,}", text)
            if w.lower() not in STOPWORDS
        )
    return [word for word, _ in Counter(words).most_common(top_n)]


def print_cluster_summary(cluster_id, tweets, labels):
    cluster_tweets = [t for t, l in zip(tweets, labels) if l == cluster_id]
    texts          = [t["text"] for t in cluster_tweets]
    keywords       = get_keywords(texts)
    avg_likes      = sum(t["likes"] for t in cluster_tweets) / len(cluster_tweets)
    top_tweets     = sorted(cluster_tweets, key=lambda t: t["likes"], reverse=True)

    print(f"\n{'─' * 60}")
    print(f"District {cluster_id}  ·  {len(cluster_tweets)} tweets  ·  avg {avg_likes:.0f} likes")
    print(f"Keywords: {', '.join(keywords)}")
    for tweet in top_tweets[:EXAMPLES_PER_CLUSTER]:
        preview = tweet["text"][:140].replace("\n", " ")
        print(f"  [{tweet['likes']:,} ♥]  {preview}...")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    import umap
    import hdbscan
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm

    print("=" * 60)
    print("Script 03 v2 — Map the Sample (Two-stage UMAP + HDBSCAN)")
    print("=" * 60)

    # ── Load ─────────────────────────────────────────────────────────
    print(f"\nLoading embeddings: {INPUT_EMBS}")
    embeddings = np.load(INPUT_EMBS)
    print(f"Shape: {embeddings.shape}")

    with open(INPUT_META, "r", encoding="utf-8") as f:
        tweets = json.load(f)
    print(f"Tweets: {len(tweets):,}")

    # ── Stage 1: UMAP 768D → 15D for clustering ───────────────────────
    print(f"\n[Stage 1] UMAP {embeddings.shape[1]}D → {UMAP_CLUSTER_N_COMPONENTS}D for clustering...")
    print(f"  n_neighbors={UMAP_CLUSTER_N_NEIGHBORS}, min_dist={UMAP_CLUSTER_MIN_DIST}")
    reducer_cluster = umap.UMAP(
        n_components=UMAP_CLUSTER_N_COMPONENTS,
        n_neighbors=UMAP_CLUSTER_N_NEIGHBORS,
        min_dist=UMAP_CLUSTER_MIN_DIST,
        metric="cosine",
        random_state=42,
    )
    embedding_15d = reducer_cluster.fit_transform(embeddings)
    print(f"  Done. Shape: {embedding_15d.shape}")

    # ── HDBSCAN on 15D space ──────────────────────────────────────────
    print(f"\n[Stage 1] HDBSCAN on {UMAP_CLUSTER_N_COMPONENTS}D space...")
    print(f"  min_cluster_size={HDBSCAN_MIN_CLUSTER_SIZE}, min_samples={HDBSCAN_MIN_SAMPLES}")
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(embedding_15d)

    cluster_ids = sorted(set(labels))
    n_clusters  = len([l for l in cluster_ids if l != -1])
    n_noise     = sum(1 for l in labels if l == -1)
    print(f"\n  Neighbourhoods found: {n_clusters}")
    print(f"  Standalone / noise:   {n_noise} ({100*n_noise/len(labels):.1f}%)")

    # ── Stage 2: UMAP 768D → 2D for visualisation ────────────────────
    print(f"\n[Stage 2] UMAP {embeddings.shape[1]}D → 2D for layout visualisation...")
    print(f"  n_neighbors={UMAP_VIZ_N_NEIGHBORS}, min_dist={UMAP_VIZ_MIN_DIST}")
    reducer_viz = umap.UMAP(
        n_components=UMAP_VIZ_N_COMPONENTS,
        n_neighbors=UMAP_VIZ_N_NEIGHBORS,
        min_dist=UMAP_VIZ_MIN_DIST,
        metric="cosine",
        random_state=42,
    )
    coords = reducer_viz.fit_transform(embeddings)
    print(f"  Done. Shape: {coords.shape}")

    # ── Print neighbourhood summaries ────────────────────────────────
    print(f"\n{'=' * 60}")
    print("NEIGHBOURHOOD SUMMARIES — the districts of Threadthulhu City")
    print(f"{'=' * 60}")
    for cluster_id in cluster_ids:
        if cluster_id == -1:
            continue
        print_cluster_summary(cluster_id, tweets, labels)

    # ── Save mapped data ──────────────────────────────────────────────
    result = []
    for i, tweet in enumerate(tweets):
        result.append({
            **tweet,
            "x":       float(coords[i, 0]),
            "y":       float(coords[i, 1]),
            "cluster": int(labels[i]),
        })
    with open(OUTPUT_MAP, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nMapped data saved to: {OUTPUT_MAP}")

    # ── Scatter plot ──────────────────────────────────────────────────
    print("Generating map visualisation...")

    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor("#0d0d0d")
    ax.set_facecolor("#0d0d0d")

    colors    = cm.tab20(np.linspace(0, 1, max(n_clusters, 1)))
    labels_np = np.array(labels)

    noise_mask = labels_np == -1
    if noise_mask.any():
        ax.scatter(
            coords[noise_mask, 0], coords[noise_mask, 1],
            c="#333333", s=2, alpha=0.4, label=f"Standalone ({n_noise})",
        )

    for i, cluster_id in enumerate([l for l in cluster_ids if l != -1]):
        mask           = labels_np == cluster_id
        cluster_tweets = [t for t, l in zip(tweets, labels) if l == cluster_id]
        kw             = get_keywords([t["text"] for t in cluster_tweets], top_n=2)
        label_text     = f"D{cluster_id}: {' · '.join(kw)} ({mask.sum()})"
        ax.scatter(
            coords[mask, 0], coords[mask, 1],
            c=[colors[i % 20]], s=5, alpha=0.7, label=label_text,
        )

    ax.set_title(
        "Threadthulhu City — Sample Map\n(3,000 tweets · Two-stage UMAP + HDBSCAN)",
        color="white", fontsize=13, pad=12,
    )
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.legend(
        bbox_to_anchor=(1.02, 1), loc="upper left",
        fontsize=7, framealpha=0.2, labelcolor="white", facecolor="#1a1a1a",
    )

    plt.tight_layout()
    plt.savefig(OUTPUT_PLOT, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Map saved to: {OUTPUT_PLOT}")
    plt.show()

    print("\n" + "=" * 60)
    print(f"Found {n_clusters} districts. Review the summaries above.")
    print("Aiming for 8-15 coherent neighbourhoods.")
    print("")
    print("Too many districts? Raise HDBSCAN_MIN_CLUSTER_SIZE")
    print("Too few districts?  Lower HDBSCAN_MIN_CLUSTER_SIZE")
    print("=" * 60)


if __name__ == "__main__":
    main()
