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

**Completed session 02:** Full archive mapped. 206,132 tweets · 61 districts · 64.7% standalone.
See `docs/session-02-full-archive-map.md` for full details.

**Key findings:**
- D4 is Pragya's own district (Visa tweets at/about her enough to cluster)
- D6 is Venkatesh Rao's district
- Recognisable neighbourhoods: Singapore, parenting, sleep, music, gaming, books, writing, money, food, gender, friends, fear, meta-Twitter
- `https` was polluting labels — fixed in stopwords
- 15D UMAP cached to `data/_umap_15d.npy` for fast re-runs

### Session 02 — March 20, 2026
**Status:** Complete. Full city map generated.
**Next session (03):** React + Pixi.js frontend. Scaffold, load data, render dots, zoom/pan, district labels.
**Key question for session 03:** What does it feel like to move around in the city?

### Session 03 — March 20, 2026
**Status:** Complete. City renders in browser. District names decided. Tooltips next.

**What was built:**
- `pipeline/06_export_frontend_data.py` — splits full_mapped.json into 3 browser files
- `frontend/` — full React + Pixi.js frontend scaffolded from scratch
  - `index.html` — dark background, fullscreen canvas
  - `src/main.jsx` — React entry point
  - `src/App.jsx` — Pixi.js city renderer (all logic lives here)
- `frontend/public/points.json` (~15MB), `districts.json` (tiny), `tweets.json` (~50MB)

**Key technical decisions:**
- Pixi.js v7 + pixi-viewport v5 (use `--legacy-peer-deps` for install)
- One Graphics object per district = one draw call per colour = fast rendering
- Coordinates normalised 0–1 in export, multiplied by WORLD_SIZE=8000 in frontend
- Viewport fitted to actual data bounding box (not full world) + 5% padding
- tweets.json lazy-loaded on first click, cached in `appRef._tweetsCache`
- Labels scale inversely to viewport zoom (consistent on-screen size)
- Landmark sizing: >10k likes=4px, >2k=3px, >500=2.2px, else 1.8px

**Bugs fixed:**
- `RangeError: Maximum call stack size exceeded` — `Math.min(...206k items)` blows JS stack → replaced with manual forEach loop
- City had too much empty space → viewport.fit() on actual data bounding box
- Labels only visible when zoomed in → lowered fade threshold 0.06 → 0.03
- Tweet panel off-screen → moved to top-right
- URLs in tweet text not clickable → split on URL regex, wrap in `<a>` tags

**District naming — 28 clusters → 24 named + The Agora:**
- D00, D20, D26, D27 merged into **The Agora** (reply conversations, not thematic content)
- D05 → **The Animal Kingdom** (not "wife" — Visa tweets about animals with/to his wife)
- D06 → **Deep Dive District** (self-reply threading artifact, not about Visa himself)
- Full name list in `docs/session-03-frontend.md`

**Decision: hover tooltips for district descriptions**
- Names like "The Marketplace", "The Interior" are evocative but not obvious
- One-sentence descriptions will appear on label hover
- Keeps map clean — meaning is one hover away

**Design status open:**
- `cluster_top` (28 districts) shown at city view; `cluster_sub` (61 sub-districts) zoom switch — not yet implemented
- Filled district regions instead of dots — not yet implemented
- Fog of war — not yet implemented

**Next session (04):**
1. Write one-sentence descriptions for all 24 districts + The Agora
2. Implement district hover tooltips
3. Sub-district zoom switching (cluster_top → cluster_sub at threshold)
4. Begin visual identity — filled district regions

### Session 04 — March 22, 2026
**Status:** Complete. City fully interactive — district panel, explorer trail, reply chains, visited glow, city lights aesthetic.

**What was built:**

**District descriptions (all 24 + The Agora):**
- Written one-sentence descriptions for every district in `DISTRICT_INFO` in `App.jsx`
- Descriptions appear in the left-side district panel on hover/click

**District hover panel (left side):**
- Replaces the tooltip approach — full panel with: district name, description, tweet count, year range, avg/peak likes, top 5 keywords, top tweet excerpt
- "Fly in ↗" button — animates viewport to district centroid at 2.5× zoom
- "Explore a thread →" button — picks a random tweet from that district and displays it

**Grid-based hover detection:**
- 300×300 grid map built at load time; each cell stores majority district
- Pointer → world coords → grid cell → district id in O(1) — no per-frame scan
- 200ms debounce: fast cursor sweeps don't trigger panel flicker

**Pinned vs hovered district logic:**
- Click a tweet → that district becomes "pinned" (stays visible)
- Hover a different district while pinned → "now entering · [name]" toast appears (top center)
- Keeps panel stable while exploring

**Explorer's Trail (right sidebar):**
- Every clicked tweet is prepended to a persistent trail (capped at 50)
- Trail stored in `localStorage` — survives page refresh
- Sidebar toggle button (bottom right) — shows/hides the full scrollable list
- Click any trail entry to re-read that tweet

**Visited tweet glow:**
- Clicked tweet ids stored in `localStorage` as `threadthulhu_visited`
- Each tick: visited dots redrawn with a pulsing glow (sine wave, ~4× larger)
- Additive blend — visited dots glow warm white against the dark canvas

**Reply chain visualization:**
- Click a tweet → parent reply lines drawn (bright warm white, 4px)
- Child reply lines drawn (amber, 3px) — up to 30 children shown
- Glow dot on clicked tweet, endpoint dots on parents and children
- Lines fade in/out smoothly (ticker lerp)
- `connections.json` loaded at startup (graceful fallback if missing)

**City lights aesthetic (visual overhaul):**
- All district dots → warm white (0xffe8c0) with additive blend → glows brightest at dense centres
- Background deep navy (0x080810) instead of near-black — subtle blue atmosphere
- Standalone dots dimmed to 15% opacity — they're city fabric, not noise
- District region tints: soft colour circles (α=0.07, radius=22) per district point
  - Overlapping circles build up colour organically at cluster centres
  - Fades in at overview scale (< 0.10), fully gone by 0.30 — colour only visible from far away

**Double-click to zoom:**
- Double-clicking empty space zooms to that district's centroid (scale 2×)
- Only fires at overview scale (< 1.5) to avoid conflicting with tweet clicking

**Typography:**
- Added Cinzel (serif caps) + Spectral (italic body) from Google Fonts via `index.html`
- All UI elements use these fonts — map aesthetic, not tech UI

**Pipeline updates (`pipeline/06_export_frontend_data.py`):**
- Exports `sub_districts.json` — 61 sub-district centroids + keywords (ready for zoom switching)
- Exports `connections.json` — flat int array of reply connections with road type:
  - type 2 = highway (cross-district reply)
  - type 1 = street (same district, different sub)
  - type 0 = alley (same sub-district)

**Key technical decisions:**
- Grid hover map (300×300 Int16Array) — O(1) hover lookup, no frame scanning
- Pixi `BLEND_MODES.ADD` on district dots — makes overlapping lights bloom naturally
- `pinnedDistrict` vs `hoveredDistrict` state — panel stays stable on click, updates on wander
- Trail entries store colour + district name at read time — survives district rename

**Design status open:**
- Sub-district zoom switching — `sub_districts.json` is exported and ready; frontend not yet wired
- Canvas district labels (text drawn on map, not just in side panel) — not yet implemented
- Fog of war — not yet implemented

**Next session (05):**
1. Sub-district zoom switching — at ~2–3× zoom, swap to 61 sub-district labels on canvas
2. Canvas district name labels — Pixi Text objects at centroid positions, scale-invariant
3. Fog of war — unvisited districts rendered dim; visited ones fully lit

### Session 05 — March 22, 2026
**Status:** Complete. Full assembly animation built. Bugs deferred.

**What was built:**

**Pipeline change:**
- Added `yr` (year, int) field to every point in `points.json` via `pipeline/06_export_frontend_data.py`
- Re-ran pipeline — `points.json` now 16.7MB (was 15MB)

**Assembly animation — 5-phase intro sequence:**

Phase 1 — Stillness (2.2s):
- Title "Threadthulhu" + subtitle "A cartography of @visakanv" fade in from centre on pure darkness
- Connection mesh (`netG`) built silently during this pause — 59k line segments, two passes:
  - Local connections (streets + alleys): 0.7px, 0.09α
  - Highways (cross-district): 0.9px, 0.14α — these form the spines shooting to edges
- `netG.alpha = 0.001` (pre-warms GPU during stillness, prevents upload stutter on reveal)
- All real city layers hidden; `_introPlaying` flag suppresses regionsG ticker

Phase 2 — Time build (6s):
- Dots accumulate year by year, 2010 → 2024
- Equal time per year (not equal points) — each year gets ~400ms regardless of tweet count
- Ticker-based continuous reveal with accumulation: never clears animG, only draws NEW dots each frame — O(new) not O(total)
- Standalone tweets (ct === -1) subsampled at 50% to halve draw-call count
- Year label updates only when year changes (not 60fps)

Phase 3 — Network reveal (0.9s fade-in):
- All 59k connections fade in over the accumulated dots
- The full nebula: dense warm centre, spines radiating to edges
- Reference screenshot: Screenshot 2026-03-20 193533.png

Phase 4 — Hold (2s):
- The nebula is visible in full. No UI. Just the image.

Phase 5 — Crossfade (0.8s):
- animG + netG fade out simultaneously
- Real city layers fade in
- `_introPlaying` flag released; regionsG ticker resumes

**Year progress bar:**
- Positioned at bottom of screen during time build only
- Large glowing year number, thin track with tick marks per year, filled bar + glow cursor
- Both bar and cursor use `transition: 0.4s linear` — stay in sync

**UI gating:**
- All panels, trail, hints hidden until introPhase === 'done'
- Intro overlay centred on screen; hides when done

**Known bugs (deferred to session 06):**
- Pulsing visited glow dots not working (String key fix attempted but didn't resolve)
- "Fly in ↗" button not working (`_flyTo` rewritten with raw viewport math but still failing)
- Both bugs are non-blocking — city is fully explorable without them

**Known performance issue (deferred, fix documented in memory):**
- Minimal lag in final second of time build (~2023-2024)
- Cause: accumulated animG Graphics object with ~100k draw calls
- Fix when ready: RenderTexture baking per year batch

**Ideas banked this session (saved to memory):**
- City assembles on load ✓ (built)
- Time Traveller mode (year slider on city)
- The Oracle (semantic search → lights up dots)
- Bridges page — cross-district connections as architectural feature, Roam-style graph
- Bridges as a whole concept: Pragya loves actual bridges, they should be a centrepiece

**Next session (06):**
1. Fix pulsing visited dots
2. Fix fly in button
3. Commit + push to GitHub
4. Begin deployment (fix .gitignore, upload tweets.json to GitHub Releases, Vercel)
