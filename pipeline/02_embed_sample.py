"""
Script 02 — Embed a Sample of Tweets
=====================================

INPUT:  data/tweets_cleaned.json  (output of 01_parse_archive.py)
OUTPUT: data/sample_tweets.json   — the sampled tweets (metadata only)
        data/sample_embeddings.npy — the embedding vectors (numpy array)

WHAT THIS DOES:
    Takes a random sample of tweets and converts each one into a vector using
    a sentence-transformer model. These vectors are the foundation of the city:
    semantically similar tweets will have similar vectors, and when we project
    them into 2D space (next script), they'll end up close together on the map.

WHY SAMPLE FIRST:
    Embedding all 247k tweets takes 20-30 minutes even on GPU. Running on a
    sample (~3,000 tweets) takes seconds and lets us validate that the
    clustering makes sense before committing to the full run. If the sample
    produces garbage clusters, we adjust parameters. If it looks good, we
    proceed to the full embed (script 04).

THE MODEL — all-mpnet-base-v2:
    Microsoft's MPNet fine-tuned for semantic similarity. It produces 768-
    dimensional vectors that capture meaning, not just keywords. Two tweets
    about "learning to focus" and "eliminating distractions" will have similar
    vectors even if they share no words. This is what makes UMAP produce a
    genuine city of ideas rather than a word-frequency map.

    It runs locally — no API key, no cost, no data leaves your machine.

REQUIRES:
    - PyTorch with CUDA installed (see requirements.txt)
    - pip install -r requirements.txt
"""

import json
import random
import numpy as np
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

DATA_DIR    = Path(__file__).parent.parent / "data"
INPUT_FILE  = DATA_DIR / "tweets_cleaned.json"
OUTPUT_META = DATA_DIR / "sample_tweets.json"
OUTPUT_EMBS = DATA_DIR / "sample_embeddings.npy"

# Number of tweets to sample. 3,000 is enough to see neighbourhood structure
# while running in under a minute on GPU. Increase to 5,000 for more fidelity.
SAMPLE_SIZE = 3000

# The embedding model. all-mpnet-base-v2 produces 768-dim vectors and is the
# best free model for semantic clustering tasks.
MODEL_NAME = "all-mpnet-base-v2"

# Batch size for encoding. 64 is a safe default for most NVIDIA GPUs.
# If you get out-of-memory errors, reduce to 32.
BATCH_SIZE = 64

# Random seed for reproducibility — same seed = same sample every time.
RANDOM_SEED = 42

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Script 02 — Embed Sample Tweets")
    print("=" * 60)

    # ── Load cleaned tweets ──────────────────────────────────────────
    print(f"\nLoading cleaned tweets from:\n  {INPUT_FILE}")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        tweets = json.load(f)
    print(f"Loaded {len(tweets):,} tweets")

    # ── Sample ───────────────────────────────────────────────────────
    random.seed(RANDOM_SEED)
    sample_size = min(SAMPLE_SIZE, len(tweets))
    sample = random.sample(tweets, sample_size)
    print(f"Sampled {sample_size:,} tweets (seed={RANDOM_SEED})")

    # Save sample metadata (id, text, date, likes) for later use in visualisation
    sample_meta = [
        {"id": t["id"], "text": t["text"], "date": t["date"], "likes": t["likes"]}
        for t in sample
    ]
    with open(OUTPUT_META, "w", encoding="utf-8") as f:
        json.dump(sample_meta, f, indent=2, ensure_ascii=False)
    print(f"Sample metadata saved to: {OUTPUT_META}")

    # ── Load model ───────────────────────────────────────────────────
    import torch
    from sentence_transformers import SentenceTransformer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        print("\nWARNING: CUDA not available — running on CPU. This will be slow.")
        print("See requirements.txt for how to install PyTorch with CUDA support.")
    else:
        gpu_name = torch.cuda.get_device_name(0)
        print(f"\nGPU detected: {gpu_name}")

    print(f"\nLoading model: {MODEL_NAME}")
    print("(First run downloads ~420MB — subsequent runs use cached copy)")
    model = SentenceTransformer(MODEL_NAME, device=device)

    # ── Embed ────────────────────────────────────────────────────────
    texts = [t["text"] for t in sample]

    print(f"\nEmbedding {len(texts):,} tweets (batch_size={BATCH_SIZE})...")
    embeddings = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,  # unit vectors work better with cosine UMAP
    )

    print(f"\nEmbeddings shape: {embeddings.shape}")
    # Should be (3000, 768) — 3000 tweets × 768 dimensions

    # ── Save ─────────────────────────────────────────────────────────
    np.save(OUTPUT_EMBS, embeddings)
    print(f"Embeddings saved to: {OUTPUT_EMBS}")
    print(f"File size: {OUTPUT_EMBS.stat().st_size / 1024 / 1024:.1f} MB")

    print("\nNext step: run 03_visualize_sample.py")


if __name__ == "__main__":
    main()
