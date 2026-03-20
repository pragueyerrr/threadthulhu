# Project Context: Threadthulhu City Map
## Conversation Log & Decision Trail

This document captures the full thinking behind this project — how the idea evolved, key decisions, references, and open questions. Use this to onboard Claude Code at the start of each session.

---

## Origin

Builder (**Pragya**) had been building a job scraper app personalized for friends — exploring new things with Claude Code. She shared a tweet thread by **@visakanv** (Visakan Veerasamy) and asked for thoughts, which led to a conversation about what could be built for him.

She reached out to Visa directly and asked: *"If I could build you something, what would it look like?"* He didn't quite know, but linked two threads. Those threads became the brief.

---

## The Two Source Threads

### Thread 1: Graph Paper / Spatial Information
**URL:** https://x.com/visakanv/status/1329093575649370113
**Date:** November 2020

**Core ideas:**
- Graph paper / infinite 2D canvas is massively underrated as an information interface
- Linear Twitter threads and flat web pages waste cognitive and organizational potential
- The r/place example: 1000x1000 pixel canvas with dense layered meaning, navigable by zoom
- Tools mentioned: Google Sheets (can stuffed into each cell), iA Writer, paper notebooks
- Key tension: **density vs. navigability** — there needs to be a balance
- Zoom level IS the interface — you don't show everything at once, you let people choose depth
- Someone had already tried to make a "map of @visakanv memespace" manually (referenced in replies)

### Thread 2: Browser Tab as Video Game
**URL:** (Jan 2015 thread)

**Core ideas:**
- Dream: a "game" in a browser tab that feels like a video game dashboard
- RTD (real-time dashboard) designed by a game company
- Inspired by: Civilization's city-building, Pokémon's satisfying auto-click progression, WoW's character that visibly reflects growth
- Ideas don't go from 0→done, they "increase their power level" over time
- Key feeling: satisfying, sense of discovery, visible progression
- Unity vs Super Mario Maker referenced

---

## Key References

### Venkatesh Rao on Visa's Archive
From venkateshrao.com:

> "Visa took the basic linear threading idea pioneered by Marc and turned it into a dizzying artform, turning his account into a tangled, densely interlinked, quote-linked, promiscuously forking Lovecraftian monstrosity of a twitter hyperobject. I came up with a term for it: *threadthulhu*."

> "I doubt Visa's insane threadthulhu can be killed at all, let alone properly butchered into a book-like echo like this one. I vibecoded the pipeline that created this book, but it will probably take AGI to similarly tame Visa's threadthulhu."

> "Visa's threadthulhu will remain forever untamed. If X dies, it will ascend into the latent spaces of various LLMs as an eternal monster."

**Key implication:** Don't try to tame it. Build it a map instead. Maps are honest about incompleteness.

### Tweetscope
**URL:** https://tweetscope.maskys.com/datasets/defenderofbasic/explore/scopes-001
Someone built a spatial/scope-based explorer of a Twitter archive — directly in this territory. Worth studying as reference/prior art.

---

## Conceptual Evolution

### Step 1: Spatial canvas
Started with the graph paper thread — the idea of a 2D zoomable canvas where tweets live spatially, clustered by theme.

### Step 2: City metaphor
The city map emerged as the right metaphor because:
- Cities are navigable without being fully knowable
- They have neighborhoods (themes), streets (connections), landmarks (famous threads), hidden alleys (obscure gems)
- They feel lived-in, not engineered
- Civilization's city-building mechanic maps perfectly onto Visa's intellectual progression

### Step 3: Game feel
The second thread added the game layer — this isn't just a visualization, it's an experience. Movement should feel like exploration, not scrolling. Discovery should feel satisfying.

### Step 4: Map framing (the key unlock)
**Maps are honest about incompleteness.** This resolved the tension between density and navigability. You don't need to show everything — you need to make exploration possible. Fog of war, landmarks, hidden alleys all follow from this.

---

## Design Decisions Made

| Decision | Choice | Reason |
|----------|--------|--------|
| Metaphor | City map | Navigable, honest about incompleteness, matches game feel |
| Visual style | Civilization meets old illustrated city maps | Feels like an artifact, not a dashboard |
| Neighborhoods | Data-driven (clustering output) | Don't pre-decide themes — let the archive speak |
| Time axis | Older = established, newer = frontier | Reflects actual intellectual evolution |
| Zoom | The primary interface | From graph paper thread — zoom level IS the interface |
| Fog of war | Unread threads dimly visible | Makes exploration meaningful |

---

## Design Decisions Still Open

- What clustering algorithm? (k-means, UMAP, hierarchical?)
- How many neighborhoods? (Could be 8-15 major districts)
- What does "fog of war" actually look like visually?
- Is there a user account / persistence layer, or is it stateless?
- Does Visa himself get a special view (his own city from the inside)?
- Mobile vs desktop priority?
- Does it update in real-time as he posts?

---

## Data

- **Source:** Community Archive (communityarchive.org) — Visa's full archive is available
- **Access:** Builder is close friends with Visa and can request archive directly
- **Scale:** 270,000+ posts over 15+ years
- **Challenge:** Venkatesh notes the archive is unusually complex — highly interlinked, quote-threaded, forking

---

## Technical Stack

- **Development:** Claude Code (vibecoding everything)
- **Frontend:** React
- **Visualization:** D3 or canvas library (TBD based on plan mode output)
- **Embeddings:** Semantic clustering of tweets (Claude API or similar)
- **Build approach:** Layer by layer — data first, then canvas, then visuals, then game feel

---

## How to Use This Document

At the start of each Claude Code session:
```
Read CONTEXT.md and BRIEF.md first. 
Then [specific task for this session].
Do not write any code until you have confirmed you understand the project.
```

Update this document after each significant session with:
- What was built
- What decisions were made
- What was learned (especially from the data/clustering)
- What the next session should tackle

---

## Session Log

### Session 0 — March 19, 2026
**Status:** Pre-build. Concept fully formed. Documents created. Architecture planned and approved.

**Decisions made this session:**
- Embeddings: sentence-transformers `all-mpnet-base-v2` (local, free, CUDA-accelerated on Pragya's NVIDIA GPU — ~20-30 min for full archive)
- Rendering: Pixi.js (WebGL) — necessary for 270k data points at 60fps
- Fog of war: local storage (persistent per browser, no backend needed)
- Deployment: Vercel — static site, pre-processed JSON committed as assets
- Visa knows the project exists and can share archive directly

**Next session:** Get archive from Visa (or communityarchive.org) → inspect format → write Python parser → embed 1,000 tweet sample → run UMAP → see what neighborhoods emerge.
**Key question for next session:** What does the archive data actually look like? What format, what fields?

### Session 01 — March 19, 2026
**Status:** Data pipeline scripts written. Ready to run.

**Archive inspected:**
- 259,083 total tweets · 247,011 original English after filtering
- Date range: Jan 2019 – Sep 2024 (only 5.5 years — archive may be partial)
- Top tweet: 183,042 likes
- Source: `visakanv_twitter_archive.json` (Community Archive format)

**Files created:**
- `pipeline/requirements.txt` — Python deps + CUDA install notes
- `pipeline/01_parse_archive.py` — parse & clean raw JSON
- `pipeline/02_embed_sample.py` — embed 3k sample with all-mpnet-base-v2
- `pipeline/03_visualize_sample.py` — UMAP + HDBSCAN + scatter plot
- `docs/architecture.md` — full architecture reference
- `docs/session-01-data-pipeline.md` — detailed session log

**Next session (02):** Run the pipeline → inspect neighbourhood output → embed full archive → build React + Pixi.js canvas skeleton.
**Key question for session 02:** What are the actual neighbourhoods? What does Visa's city look like?

**Iteration log:**
- v1 (HDBSCAN on 2D UMAP) failed — 87% of tweets collapsed into one blob
- v2 (two-stage: 15D UMAP for clustering + 2D UMAP for layout) worked — 29 districts on 3k sample
- Screenshots: `docs/screenshots/sample-map-v1-blob.png`, `docs/screenshots/sample-map-v2-two-stage.png`
- Full archive embed (script 04) currently running — ~25 min on GPU
- Next: script 05 (map full archive), then React + Pixi.js frontend
