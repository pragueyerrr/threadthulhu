# Threadthulhu City Map — Architecture Reference

*Created: Session 01 (March 19, 2026). Update this document when major architectural decisions change.*

---

## What We're Building

An explorable, game-like city that *is* Visakan Veerasamy's mind — built from his tweet archive, navigable like Civilization, where the shape of the city reflects the shape of his thinking. Not a data dashboard. An artifact. A world.

**The core insight:** UMAP (a dimensionality reduction algorithm) takes tweet vectors and produces 2D coordinates where semantically similar tweets end up spatially close. The city layout is not designed — it *emerges* from the data. The map is literally the shape of his thinking.

---

## System Overview

```
Raw Archive JSON
      │
      ▼
[01] Parse & Clean         → data/tweets_cleaned.json
      │
      ▼
[02] Embed (sample)        → data/sample_embeddings.npy
      │                       data/sample_tweets.json
      ▼
[03] UMAP + HDBSCAN        → data/sample_mapped.json
     (sample, validate)       data/sample_map.png
      │
      │  (if clustering looks good)
      ▼
[04] Embed Full Archive    → data/full_embeddings.npy   [TODO]
      │
      ▼
[05] Map Full Archive      → data/full_mapped.json      [TODO]
      │
      ▼
[React App]                → Pixi.js city rendering     [TODO]
      │
      ▼
[Vercel Deploy]            → shareable link for Visa    [TODO]
```

---

## Data Pipeline (Python)

**Location:** `pipeline/`

**Why Python:** Best ML tooling ecosystem — umap-learn, hdbscan, sentence-transformers, numpy all have mature, well-documented Python libraries. None of this exists in the Node.js ecosystem.

### Script 01 — Parse & Clean (`01_parse_archive.py`)
- Loads the raw Community Archive JSON (~1GB)
- Filters: removes retweets, non-English tweets, very short tweets
- Normalizes dates to ISO 8601
- Flags self-replies (thread continuations)
- Saves a flat JSON list of tweet objects

### Script 02 — Embed Sample (`02_embed_sample.py`)
- Samples 3,000 tweets (fast iteration before full embed)
- Loads sentence-transformer model `all-mpnet-base-v2`
- Encodes tweets into 768-dimensional vectors
- Saves vectors as numpy `.npy` array

### Script 03 — Visualize Sample (`03_visualize_sample.py`)
- Runs UMAP: 768 dimensions → 2D coordinates
- Runs HDBSCAN: finds natural clusters (neighbourhoods)
- Prints neighbourhood keyword summaries
- Saves scatter plot image for human review
- Outputs `sample_mapped.json` (tweets + x/y + cluster ID)

### Script 04 — Embed Full Archive (`04_embed_full.py`) — *TODO*
- Same as script 02 but for all ~247k tweets
- Runs in batches with progress tracking
- Uses CUDA GPU (NVIDIA) — estimated 20-30 minutes

### Script 05 — Map Full Archive (`05_map_full.py`) — *TODO*
- UMAP + HDBSCAN on full embeddings
- Produces the authoritative city layout data

---

## Embedding Model

**Model:** `sentence-transformers/all-mpnet-base-v2`

- **Dimensions:** 768
- **Why this model:** Trained specifically for semantic similarity. Captures meaning, not just keywords — "learning to focus" and "eliminating distractions" produce similar vectors even with no shared words.
- **Cost:** Free, runs locally, no API key needed
- **Speed:** ~20-30 min for 247k tweets on NVIDIA GPU (Pragya's machine has NVIDIA + CUDA)
- **Alternative considered:** OpenAI text-embedding-3-small (~$0.26 total) — rejected in favour of local to keep everything self-contained

---

## Dimensionality Reduction — Two-stage UMAP

**Why UMAP over alternatives:**
- PCA would lose too much semantic structure (it's linear)
- t-SNE doesn't preserve global structure (districts near each other on the map wouldn't be conceptually related)
- UMAP preserves both local structure (tweets about the same thing cluster) AND global structure (related clusters are near each other). This makes it a genuine map, not just a scatter plot.

**Why two stages (learned in session 01):**
The naive approach — UMAP to 2D then HDBSCAN — collapses too much structure.
87% of the sample ended up in one cluster. The fix is to separate the two jobs:

| Stage | Purpose | Output dimensions | Key parameters |
|-------|---------|-------------------|----------------|
| UMAP (cluster) | Find semantic structure | 768D → 15D | n_neighbors=30, min_dist=0.0 |
| HDBSCAN | Label districts | — | min_cluster_size=15 |
| UMAP (viz) | Draw the map | 768D → 2D | n_neighbors=15, min_dist=0.1 |

This is standard practice in single-cell biology (the field with the most UMAP+HDBSCAN experience) and produced 29 coherent districts vs. 1 blob in testing.

**Output:** 2D (x, y) coordinates per tweet (from viz UMAP). Cluster ID from HDBSCAN on 15D space. Both stored in the mapped JSON.

---

## Clustering — HDBSCAN

**Why HDBSCAN over k-means:**
- k-means requires specifying the number of clusters in advance — we don't know how many districts the city should have
- HDBSCAN finds natural density-based clusters, handles clusters of different sizes and shapes, and labels outliers as "noise" (standalone buildings / hidden alleys)
- The number of districts emerges from the data

**Key parameters:**
- `min_cluster_size=20` — minimum tweets to form a district. Raise to merge small clusters.
- `min_samples=5` — raise for more conservative clustering

**Output:** A cluster ID per tweet. -1 = noise (standalone building). 0, 1, 2... = districts.

---

## Frontend

**Framework:** React + Vite
**Renderer:** Pixi.js (WebGL)

**Why Pixi.js over D3 or Canvas 2D:**
With ~247k tweets rendered as city elements, D3 SVG will completely choke (SVG can handle ~10k elements before becoming sluggish). Plain Canvas 2D struggles at scale too. Pixi.js uses WebGL under the hood and can render millions of sprites at 60fps. This is not a premature optimization — it's the right foundation.

**Why Vite:**
Fast development server, excellent React support, simple static site output for Vercel deployment.

---

## Fog of War — Local Storage

Unread threads appear dimly on the map and "reveal" when visited. Persistence via browser `localStorage` — no backend, no user accounts needed. Each visitor (including Visa) gets their own exploration journey, starting with everything fogged.

This means the site is entirely stateless server-side, which allows simple Vercel deployment.

---

## Deployment

**Target:** Vercel (free tier)
**Approach:** Static site
- Python pipeline runs locally, outputs pre-processed JSON files
- JSON files committed to repo as static assets
- React/Pixi.js app reads JSON at runtime
- No server, no database, no backend

**Data loading strategy (to address large JSON):**
- Full archive data will be chunked by region (spatial tiles) and loaded on demand as the user zooms in — prevents shipping all 247k tweets to the browser upfront.

---

## Data

**Source:** Community Archive / Twitter data export
**Format:** Community Archive JSON — `{ tweets: [{ tweet: {...} }] }`
**Scale:** ~259k tweets total, ~247k original English tweets after filtering
**Date range:** Jan 2019 – Sep 2024 (archive appears to start mid-career, not from 2008 account creation)
**Note:** An older archive going back to 2008 would extend the city significantly. Worth asking Visa if he has one.

---

## Key Architectural Decisions Log

| Decision | Choice | Reason | Session |
|----------|--------|--------|---------|
| Embedding | local sentence-transformers | Free, private, GPU-accelerated on Pragya's machine | 01 |
| Renderer | Pixi.js (WebGL) | 247k data points at 60fps — D3/SVG can't handle it | 01 |
| Fog of war | localStorage | No backend needed, still fully persistent per browser | 01 |
| Deployment | Vercel static site | Free, dead simple, shareable link for Visa | 01 |
| Clustering | Two-stage UMAP + HDBSCAN | Single-stage 2D UMAP collapsed 87% of tweets into one blob | 01 |
