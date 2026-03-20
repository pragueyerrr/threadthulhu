# Threadthulhu City Map

An explorable city built from [@visakanv](https://x.com/visakanv)'s tweet archive.
Neighbourhoods are themes. Buildings are threads. The shape of the city is the shape of his thinking.

**Status:** actively being built. Data pipeline complete, frontend in progress.

---

## What is this?

Visakan Veerasamy has been writing on Twitter since 2008. 247k tweets, densely interlinked,
quote-threaded, forking in every direction. Venkatesh Rao once called it a threadthulhu — a
Lovecraftian hyperobject that ["will probably take AGI to properly tame."](https://venkateshrao.com/twitter-book/chapters/preface.html)

We're not trying to tame it. We're building it a map.

The idea came from two threads Visa wrote — one about infinite 2D canvases as an underrated
interface for information, one about what it would feel like if a browser tab felt like a video
game. Put those together and you get: an explorable city where every district is a cluster of ideas,
every building is a thread, and zoom level is the interface.

You can't read all of Visa's archive. Nobody can. But you can explore it — wander into
neighbourhoods you've never visited, stumble onto a thread from 2019 that changes how you think
about something, discover that two ideas you'd never connected turn out to live on the same street.

Maps are honest about incompleteness. They don't pretend to show everything. They just make
exploration possible.

---

## The city

- **Neighbourhoods** = major recurring themes, determined entirely by the data (not decided in advance)
- **Buildings** = individual threads — size reflects length and engagement
- **Landmarks** = the tweets that spread furthest, the threads most linked to
- **Hidden alleys** = obscure gems: 3 likes, quietly brilliant
- **Fog of war** = threads you haven't read yet appear dim. Explore to reveal.
- **Time as texture** = older parts of the city feel established and dense. Recent posts are the frontier.

The aesthetic is Civilization meets old illustrated city maps. Not a data dashboard. Something that
feels like an artifact.

---

## How it works technically

**Data pipeline (Python):**
1. Parse and clean the tweet archive (~247k original tweets after filtering retweets)
2. Embed every tweet into a 768-dimensional vector using `sentence-transformers/all-mpnet-base-v2` — a free, local model that encodes meaning, not just keywords
3. Run UMAP to reduce 768 dimensions to 15, preserving semantic structure
4. Run HDBSCAN to find natural clusters — these become the city's neighbourhoods
5. Run a second UMAP pass to 2D for the visual layout
6. Export to JSON for the frontend to consume

The key insight: UMAP doesn't just cluster the data — it produces spatial coordinates where semantic
distance becomes physical distance. The city layout is the shape of his thinking. It emerges from
the data; we don't design it.

**Frontend:**
- React + Vite
- Pixi.js for rendering (WebGL — necessary for 247k data points at 60fps)
- Fog of war via localStorage — no backend, no accounts, just your own exploration state in your own browser
- Deployable as a static site (Vercel)

---

## Current status

- ✅ Archive obtained and inspected (Jan 2019 – Sep 2024, 247k original tweets)
- ✅ Data pipeline written and tested on a 3,000-tweet sample
- ✅ Two-stage UMAP approach validated — 29 coherent districts visible in sample
- ✅ Full archive embedded (247k tweets, ~25 min on GPU)
- ⏳ Full archive clustered and mapped (in progress)
- ⬜ React + Pixi.js frontend
- ⬜ City rendering — buildings, streets, time axis
- ⬜ Game feel — fog of war, landmarks, movement

---

## Running it yourself

You'll need the tweet archive (not included in this repo — it's 247k of someone's personal writing).
```bash
# Install PyTorch with CUDA first (if you have an NVIDIA GPU)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# Install everything else
pip install -r pipeline/requirements.txt
```

Place the archive JSON at the project root as `visakanv_twitter_archive.json`, then:
```bash
py pipeline/01_parse_archive.py    # clean the archive
py pipeline/02_embed_sample.py     # embed a 3k sample to test
py pipeline/03_visualize_sample.py # see initial neighbourhood map
py pipeline/04_embed_full.py       # embed full archive (~25 min on GPU)
py pipeline/05_map_full.py         # map and cluster everything
```

---

## Why build this

I asked Visa if I could build him something. I knew he'd have an answer even if he couldn't fully
articulate it yet — that's just how he thinks. He linked two threads. I know my homie.

Honestly though — I'm almost addicted to this feeling. Ever since I figured out what the threads
were pointing at, I've felt something like a shot of adrenaline I couldn't shake. The kind of
excitement that's hard to explain to people who haven't felt it — like speed, but it's just an idea
that won't let you go. I needed to try. Even if it fails, even if the map is wrong or the city
doesn't render or the neighborhoods don't make sense — I am so viscerally, embarrassingly psyched
to find out.

That feeling is the whole point.

The threadthulhu doesn't need to be killed. It needs a map. And maps don't capture everything —
they just make exploration possible.

---

*Built with [Claude Code](https://claude.ai/code). Inspired by [this thread](https://x.com/visakanv/status/1329093575649370113) and [this one](https://x.com/visakanv/status/1084471331414933510?s=46). Named by [@vgr](https://x.com/vgr).*
