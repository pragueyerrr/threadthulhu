# Session 05 — Assembly Animation
*Date: March 22, 2026*
*Status: Complete. 5-phase intro animation built.*

---

## What We Built

A cinematic intro animation that plays once on load, assembling the city in front of the user before revealing the interactive map.

---

## The 5 Phases

### Phase 1 — Stillness (2.2s)
Pure darkness. "Threadthulhu / A cartography of @visakanv" fades in from centre with CSS opacity + transform transitions. While this plays, the connection mesh (59k line segments) is silently built in the background and pre-warmed on the GPU at `alpha = 0.001`.

### Phase 2 — Time Build (6s)
Dots accumulate 2010 → 2024. Key decisions:
- **Equal time per year** — each year gets ~400ms regardless of tweet count. The year counter ticks at a steady beat; dense years (2022-2024) have dots appearing faster, which is honest and cinematic.
- **Accumulation, not clear** — `animG` never clears. Each frame only draws the *new* dots since last frame (O(new) not O(total)). This kept early years smooth.
- **50% standalone subsample** — tweets with `ct === -1` (standalones, ~65% of archive) drawn at every other index. Halves draw-call count with no visible quality loss due to additive blending.
- **Year label** — updates only when year changes, not 60fps. Connected to a progress bar at the bottom of screen.

**Year progress bar:** thin track across bottom, tick mark per year, filled bar + glow cursor dot. Both use `transition: 0.4s linear` so they stay in sync as the year counter steps.

### Phase 3 — Network Reveal (0.9s)
The `netG` connection mesh fades in over the accumulated dots. Two draw passes:
- Local connections (streets + alleys): 0.7px width, 0.09α
- Highways (cross-district): 0.9px, 0.14α — these are the spines that shoot to the edges

Result: the screenshot Pragya shared (Screenshot 2026-03-20 193533.png) — a warm nebula with a bright dense centre and spines radiating outward. This is the single most striking frame of the whole experience.

### Phase 4 — Hold (2s)
Nothing. Just the nebula. No UI. The user has 2 seconds to take it in.

### Phase 5 — Crossfade (0.8s)
`animG` and `netG` fade out together. Real city layers (standaloneG, district dots, visitedG, replyChainG) fade in. The `_introPlaying` flag is released and the regionsG ticker resumes (district colour tints reappear at overview zoom). UI panels, trail, hints all fade in.

---

## Technical Notes

**`_introPlaying` flag:** Set on `appRef.current` before animation starts. The main ticker checks it before updating `regionsG` alpha. Without this, the district colour tints would be visible from frame 1 (the ticker overrides our `alpha = 0`).

**GPU pre-warm:** `netG.alpha = 0.001` (not 0) forces Pixi to upload the 59k line geometry to the GPU during Phase 1 when nothing else is happening. Without this, the first frame of Phase 3 triggers a GPU upload, causing a visible hitch.

**Known performance issue:** Minimal lag (~1s) at the very end of Phase 2. Cause: accumulated Graphics object with ~100k draw calls. Pixi replays all draw commands every frame. Fix when ready: render each year's batch to a `RenderTexture` instead of accumulating on one Graphics. Decision: deferred — the lag is small and only happens once.

---

## Pipeline Change

Added `yr` field (integer year, e.g. 2019) to every point in `points.json`. Extracted from `t["date"][:4]` in `pipeline/06_export_frontend_data.py`. Points.json grew from 15MB to 16.7MB.

---

## Ideas Banked (not built, saved to memory)

- **Time Traveller** — year slider on the city, scrub through archive history
- **The Oracle** — type a topic, semantically matching dots light up
- **Bridges** — cross-district connections as a centrepiece feature. Pragya loves bridges (actual engineering + aesthetics). Could be own page with architectural visual style + Roam-style graph view.

---

## Known Bugs (Deferred to Session 06)

| Bug | Status | Notes |
|-----|--------|-------|
| Visited glow dots not pulsing | Deferred | String key fix attempted — `_pointsById` now uses `String(p.id)`, visited set uses `String(p.id)`. Still not resolved. Likely a deeper type or scoping issue. |
| "Fly in ↗" button broken | Deferred | `vp.animate()` doesn't work in pixi-viewport v6. Rewrote with raw `viewport.x/y/scale` math. Still not firing. Investigate `d.cx` value and `appRef._flyTo` registration. |

---

## Next Session (06)

1. Fix pulsing visited dots — console.log the visited set size and pointsById lookup to find root cause
2. Fix fly in — verify `d.cx` is populated and `_flyTo` is registered on appRef
3. Commit + push session 05 to GitHub
4. Begin deployment: fix `.gitignore`, upload `tweets.json` to GitHub Releases, connect Vercel
