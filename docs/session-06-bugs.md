# Session 06 — Bug Fixes
*Date: March 22, 2026*
*Status: Complete. Four bugs fixed, one deferred.*

---

## What We Fixed

### Bug 1 — Pulsing visited dots not appearing
**Root cause:** `animG.destroy()` in the crossfade was throwing an internal Pixi error (`Cannot read properties of null (reading 'refCount')`). This crash propagated out of Pixi's `_tick` loop, killing ALL tickers — including the main ticker that clears and redraws `visitedG` each frame. With the ticker dead, `visitedG` was cleared once and never redrawn, and its alpha stayed at 0 (set to 0 at animation start, never restored).

**Debug method:** Added a 1-second throttled `console.log` inside the ticker that printed `vg.alpha`, `visitedIdsRef.current.size`, `_pointsById` lookup result, and `vg.destroyed`. The log confirmed `vg.alpha: 0` with a valid `pt` object — pointing to the alpha, not a data issue.

**Fix:** Wrapped `animG.destroy()` and `netG.destroy()` in `try/catch`. The hard-set `alpha = 1` and `resolve()` now always run.

---

### Bug 2 — Fly-in animation locking viewport (zoom and drag both broken)
**Root cause:** `app.ticker.add(fn)` in Pixi v7 returns `this` (the Ticker itself), not the listener. So `app.ticker.remove(flyId)` was passing the Ticker object as the callback — no match found, ticker never removed. The fly animation ran forever at `rawT = 1`, setting `viewport.x/y/scale` to the target position on every frame, overriding all user input.

The same bug existed in the crossfade ticker but was harmless there (at `t=1` it just sets alpha=1 repeatedly on already-faded layers).

**Fix:** Capture the callback function by name:
```javascript
const flyTick = () => { ...; if (rawT >= 1) { app.ticker.remove(flyTick); ... } }
app.ticker.add(flyTick)
```
Also fixed the crossfade with `fadeTick` for consistency. Added cancellation of any in-progress fly before starting a new one (`appRef.current._flyTick` tracking).

---

### Bug 3 — Can't zoom out after fly-in
**Root cause:** The `decelerate` plugin listens to every `moved` event from the viewport. The smooth wheel plugin emits `moved` on each per-frame position update (repositioning to keep the cursor's world point fixed during zoom). At fly-in scale (2.5), these per-frame position changes are ~180px each — the decelerate plugin records this as large drag velocity and immediately fights against the zoom-out.

At overview scale (~0.32), the same repositioning is ~6px — imperceptible, so it didn't appear broken before.

**Fix:** Reset decelerate velocity on every `zoomed` event:
```javascript
viewport.on('zoomed', () => { viewport.plugins.get('decelerate')?.reset() })
```

**Also tuned:** Zoom sensitivity changed from `percent: 0.15, smooth: 8` to `percent: 0.25, smooth: 5` for more responsive, larger per-step zoom in both directions.

---

### Bug 4 — ↩ Overview button
Added as a UX complement to the zoom fix. When zoomed in past scale 1.5 (fly-in threshold), the hint text is replaced by a "↩ overview" button that flies back to the initial overview position/scale.

Implementation:
- `appRef.current._overview = { x, y, scale }` stored after `viewport.fit()` at init
- `zoomedIn` React state, updated in the ticker only when crossing the 1.5 threshold (not every frame)
- Button calls `_flyTo(overview.x, overview.y, overview.scale, 900)`

---

## Deferred

| Item | Notes |
|------|-------|
| HD / crisp dots at all zoom levels | Attempted WebGL `gl_PointSize` shader approach — reverted. The dots are drawn at fixed world-unit radii and become sub-pixel at overview zoom. Proper fix requires either: (a) custom GL_POINTS vertex shader with `gl_PointSize` in screen pixels, or (b) LOD re-draw at zoom thresholds. Both viable but need more care. |

---

## Technical Notes

**`ticker.add()` return value gotcha:** In Pixi v7, `ticker.add(fn)` returns `this` (the Ticker), not the TickerListener. Always capture the callback function itself and pass it to `ticker.remove(fn)`. Never use the return value of `ticker.add()` as the removal handle.

**Decelerate + zoom interaction:** The decelerate plugin is designed for drag velocity, but it also receives `moved` events from other sources (including wheel zoom repositioning). At high zoom levels, zoom-induced repositioning creates large position deltas that decelerate interprets as velocity. Resetting on `zoomed` events cleanly separates drag deceleration from zoom behaviour.

---

## Next Session (07)

1. HD / crisp dots — revisit with a proper plan
2. Deployment: `.gitignore` fix, `tweets.json` to GitHub Releases, Vercel
3. Bridges feature (cross-district connections as their own page)
