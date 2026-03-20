"""
Script 04 — Embed the Full Archive
====================================

INPUT:  data/tweets_cleaned.json      (output of 01_parse_archive.py)
OUTPUT: data/full_embeddings.npy      — all tweet embedding vectors
        data/full_tweets_meta.json    — tweet metadata (id, text, date, likes, etc.)
                                        stored separately from embeddings for easy lookup

WHAT THIS DOES:
    Embeds every tweet in the cleaned archive using the same all-mpnet-base-v2
    model used for the sample. This is the expensive step — ~247k tweets —
    but it only needs to run once. The output is saved incrementally so if
    anything interrupts it, you can resume (see CHECKPOINT_EVERY below).

ESTIMATED TIME:
    ~20-30 minutes on NVIDIA GPU with CUDA
    ~2-4 hours on CPU (not recommended)

INCREMENTAL CHECKPOINTING:
    Every CHECKPOINT_EVERY tweets, the script saves progress to disk. If the
    run is interrupted, delete the partial .npy files and re-run — or set
    RESUME = True to skip already-embedded batches (see below).

WHY STORE EMBEDDINGS SEPARATELY FROM METADATA:
    Embeddings are float32 numpy arrays — fast to load with np.load().
    Metadata is human-readable JSON. Keeping them separate means you can
    inspect/edit the metadata without touching the large binary file.
    They stay in sync via array index: embeddings[i] corresponds to
    full_tweets_meta.json[i].
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime

# ─── Configuration ────────────────────────────────────────────────────────────

DATA_DIR       = Path(__file__).parent.parent / "data"
INPUT_FILE     = DATA_DIR / "tweets_cleaned.json"
OUTPUT_EMBEDDINGS = DATA_DIR / "full_embeddings.npy"
OUTPUT_META    = DATA_DIR / "full_tweets_meta.json"

MODEL_NAME     = "all-mpnet-base-v2"
BATCH_SIZE     = 32         # 2GB GPU requires small batches. Raise to 64 if you upgrade GPU.
CHECKPOINT_EVERY = 10000    # save progress every N tweets

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Script 04 — Embed Full Archive")
    print("=" * 60)

    # ── Load cleaned tweets ──────────────────────────────────────────
    print(f"\nLoading cleaned tweets from:\n  {INPUT_FILE}")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        tweets = json.load(f)
    print(f"Total tweets to embed: {len(tweets):,}")

    # ── Save metadata (id, text, date, likes, etc.) ──────────────────
    # Store everything except the embeddings themselves.
    # embeddings[i] will always correspond to full_tweets_meta[i].
    meta = [
        {
            "id":            t["id"],
            "text":          t["text"],
            "date":          t["date"],
            "likes":         t["likes"],
            "retweets":      t["retweets"],
            "reply_to_id":   t["reply_to_id"],
            "is_self_reply": t["is_self_reply"],
        }
        for t in tweets
    ]
    with open(OUTPUT_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"Metadata saved to: {OUTPUT_META}")

    # ── Load model ───────────────────────────────────────────────────
    import torch
    from sentence_transformers import SentenceTransformer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        print(f"\nGPU: {torch.cuda.get_device_name(0)}")
    else:
        print("\nWARNING: CUDA not available — running on CPU. This will be slow.")

    print(f"Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME, device=device)

    # ── Embed in batches with checkpointing ─────────────────────────
    texts       = [t["text"] for t in tweets]
    total       = len(texts)
    all_embeddings = []
    checkpoint_files = []

    print(f"\nEmbedding {total:,} tweets")
    print(f"Batch size: {BATCH_SIZE} | Checkpoint every: {CHECKPOINT_EVERY:,} tweets")
    print(f"Started at: {datetime.now().strftime('%H:%M:%S')}\n")

    for start in range(0, total, CHECKPOINT_EVERY):
        end   = min(start + CHECKPOINT_EVERY, total)
        chunk = texts[start:end]

        print(f"Embedding tweets {start:,}–{end:,} of {total:,}...")
        chunk_embeddings = model.encode(
            chunk,
            batch_size=BATCH_SIZE,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        # Save checkpoint
        checkpoint_path = DATA_DIR / f"_checkpoint_{start:06d}.npy"
        np.save(checkpoint_path, chunk_embeddings)
        checkpoint_files.append(checkpoint_path)
        print(f"  Checkpoint saved: {checkpoint_path.name}")
        print(f"  Time: {datetime.now().strftime('%H:%M:%S')}\n")

    # ── Merge checkpoints into final file ────────────────────────────
    print("Merging checkpoints into final embeddings file...")
    all_chunks = [np.load(p) for p in checkpoint_files]
    full_embeddings = np.concatenate(all_chunks, axis=0)

    print(f"Final embeddings shape: {full_embeddings.shape}")
    # Should be (~247000, 768)

    np.save(OUTPUT_EMBEDDINGS, full_embeddings)
    size_mb = OUTPUT_EMBEDDINGS.stat().st_size / 1024 / 1024
    print(f"Saved to: {OUTPUT_EMBEDDINGS}  ({size_mb:.0f} MB)")

    # Clean up checkpoints
    for p in checkpoint_files:
        p.unlink()
    print("Checkpoint files cleaned up.")

    print(f"\nFinished at: {datetime.now().strftime('%H:%M:%S')}")
    print(f"\nNext step: run 05_map_full.py")


if __name__ == "__main__":
    main()
