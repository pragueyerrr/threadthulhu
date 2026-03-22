import { useEffect, useRef, useState } from 'react'
import { Application, Graphics, BLEND_MODES } from 'pixi.js'
import { Viewport } from 'pixi-viewport'

// ── District colour palette ───────────────────────────────────────────────────
const DISTRICT_COLOURS = [
  0x4e79a7, 0xf28e2b, 0xe15759, 0x76b7b2, 0x59a14f,
  0xedc948, 0xb07aa1, 0xff9da7, 0x9c755f, 0xbab0ac,
  0x1f77b4, 0xff7f0e, 0x2ca02c, 0xd62728, 0x9467bd,
  0x8c564b, 0xe377c2, 0x7f7f7f, 0xbcbd22, 0x17becf,
  0xa55194, 0x6b6ecf, 0xb5cf6b, 0xcedb9c, 0x8ca252,
  0xbd9e39, 0xad494a, 0xd6616b,
]

const STANDALONE_COLOUR = 0x333333
const WORLD_SIZE        = 8000

// ── District names + descriptions ────────────────────────────────────────────
const DISTRICT_INFO = {
  0:  { name: 'The Agora',           desc: 'The public square — replies and conversations woven through the whole city, where Visa talks with everyone.' },
  1:  { name: 'Rock & Roll Boulevard', desc: 'Rock music, culture, and the spirit of creative rebellion — artists, musicians, and the people who do things with genuine energy.' },
  2:  { name: 'Rao Street',          desc: 'Long discourse threads in dialogue with Venkatesh Rao, exploring meta-ideas about writing, Twitter, and intellectual culture.' },
  3:  { name: 'The Long Game',       desc: 'Philosophical threads about life across years — patterns, truths, and insights that only reveal themselves over time.' },
  4:  { name: 'Broadcast Alley',     desc: 'Videos, podcasts, TikToks, and YouTube links — things worth watching, shared with commentary.' },
  5:  { name: 'The Animal Kingdom',  desc: 'Cats, birds, fish, and all creatures great and small — Visa\'s tender side as an animal enthusiast and observer.' },
  6:  { name: 'Deep Dive District',  desc: 'Long self-reply threads begun with @visakanv — his most sustained explorations of a single idea.' },
  7:  { name: 'The Arcade',          desc: 'Games, movies, and the culture of play — Visa\'s engagement with fiction, entertainment, and interactive worlds.' },
  8:  { name: 'Music Row',           desc: 'Songs, playlists, guitar, and music discovery — the soundtrack to the threadthulhu.' },
  9:  { name: 'The Night Quarter',   desc: 'Sleep, cigarettes, night hours, and the texture of daily life — the quieter, more habitual side of Visa.' },
  10: { name: 'The Marketplace',     desc: 'Money, business, marketing, and how value moves — Visa\'s thinking on economics and building things.' },
  11: { name: 'The Promenade',       desc: 'Fashion, style, hair, and how you carry yourself — aesthetic sensibility and personal presentation.' },
  12: { name: 'The Feed',            desc: 'Meta-commentary about Twitter itself — how the platform works, how to use it well, what threads do.' },
  13: { name: 'The Library Annex',   desc: 'Notes, tools, Roam Research, and personal knowledge management — the infrastructure of thinking.' },
  14: { name: 'The Library',         desc: 'Books, reading, and the written word — recommendations, reactions, and reading as a practice.' },
  15: { name: 'Writers\' Quarter',   desc: 'The craft of writing — essays, words, and the discipline of putting ideas down clearly.' },
  16: { name: 'The Coffee District', desc: 'Food, coffee, Singapore hawker culture, and the pleasures of eating and drinking.' },
  17: { name: 'Little Singapore',    desc: 'Singapore, Singaporean identity, and what it means to be from that particular city-state.' },
  18: { name: 'Rationalist Row',     desc: 'Conversations with the rationalist and EA intellectual community — a specific constellation of thinkers and their ideas.' },
  19: { name: 'The Nursery',         desc: 'Parenting, children, and being a dad — Visa\'s observations on raising kids and being raised.' },
  20: { name: 'The Agora',           desc: 'The public square — replies and conversations woven through the whole city, where Visa talks with everyone.' },
  21: { name: 'The Interior',        desc: 'Fear, self-work, and the ongoing project of becoming — the inner landscape, honestly mapped.' },
  22: { name: 'The Forum',           desc: 'Power, status, social dynamics, and how people operate in groups — Visa\'s sociology of human behaviour.' },
  23: { name: 'Friendship Park',     desc: 'Friendship as a practice — asking for things, showing up, being someone people can lean on.' },
  24: { name: 'The Commons',         desc: 'Gender, men and women, and the territory between people — candid and sometimes sharp.' },
  25: { name: 'The Hearth',          desc: 'Marriage, partnership, and long-term love — Visa and his wife, and what commitment looks like over years.' },
  26: { name: 'The Agora',           desc: 'The public square — replies and conversations woven through the whole city, where Visa talks with everyone.' },
  27: { name: 'The Agora',           desc: 'The public square — replies and conversations woven through the whole city, where Visa talks with everyone.' },
}

// Convert Pixi hex number → CSS hex string
const hexToCSS = hex => '#' + hex.toString(16).padStart(6, '0')

export default function App() {
  const containerRef      = useRef(null)
  const appRef            = useRef(null)
  const pointsDataRef     = useRef(null)
  const lastHoveredIdRef  = useRef(null)
  const tweetsByDistrictRef = useRef({})
  const visitedIdsRef     = useRef(new Set())
  const [status,          setStatus]          = useState('Loading city data...')
  const [hoveredDistrict, setHoveredDistrict] = useState(null)
  const [pinnedDistrict,  setPinnedDistrict]  = useState(null)
  const [selectedTweet,   setSelectedTweet]   = useState(null)
  const [trailOpen,       setTrailOpen]       = useState(false)
  const [trail,           setTrail]           = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('threadthulhu_trail') || '[]')
        .filter(e => e && e.id && e.text)
    } catch { return [] }
  })

  useEffect(() => {
    let app, viewport

    async function init() {
      // ── Load data ──────────────────────────────────────────────────
      setStatus('Loading points...')
      const [pointsRes, districtsRes, connRes] = await Promise.all([
        fetch('/points.json'),
        fetch('/districts.json'),
        fetch('/connections.json').catch(() => null),
      ])
      const points    = await pointsRes.json()
      const districts = await districtsRes.json()
      const connRaw   = connRes ? await connRes.json() : null
      pointsDataRef.current = points

      // Index districts by id for fast panel lookup
      const districtsById = Object.fromEntries(districts.map(d => [d.id, d]))

      // Index tweet ids by district for the Explore button
      const tweetsByDistrict = {}
      points.forEach(p => {
        if (p.ct === -1) return
        if (!tweetsByDistrict[p.ct]) tweetsByDistrict[p.ct] = []
        tweetsByDistrict[p.ct].push(p.id)
      })
      tweetsByDistrictRef.current = tweetsByDistrict

      // Build id → world position + size map for visited dot rendering
      const pointsById = {}
      points.forEach(p => {
        pointsById[p.id] = {
          wx:   p.x * WORLD_SIZE,
          wy:   p.y * WORLD_SIZE,
          size: p.l > 10000 ? 4 : p.l > 2000 ? 3 : p.l > 500 ? 2.2 : 1.8,
        }
      })

      // Load visited tweet ids from localStorage
      try {
        const saved = localStorage.getItem('threadthulhu_visited')
        if (saved) JSON.parse(saved).forEach(id => visitedIdsRef.current.add(id))
      } catch (e) {}

      setStatus('Rendering city...')

      // ── Compute tight bounding box ─────────────────────────────────
      let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity
      points.forEach(p => {
        if (p.x < xMin) xMin = p.x
        if (p.x > xMax) xMax = p.x
        if (p.y < yMin) yMin = p.y
        if (p.y > yMax) yMax = p.y
      })
      const padX = (xMax - xMin) * 0.05
      const padY = (yMax - yMin) * 0.05

      // ── Pixi application ───────────────────────────────────────────
      app = new Application({
        width:           containerRef.current.clientWidth,
        height:          containerRef.current.clientHeight,
        backgroundColor: 0x080810,
        antialias:       true,
        resolution:      window.devicePixelRatio || 1,
        autoDensity:     true,
      })
      containerRef.current.appendChild(app.view)
      appRef.current = app
      appRef.current._pointsById = pointsById
      appRef.current._viewport   = viewport

      // ── Viewport ──────────────────────────────────────────────────
      viewport = new Viewport({
        screenWidth:  app.screen.width,
        screenHeight: app.screen.height,
        worldWidth:   WORLD_SIZE,
        worldHeight:  WORLD_SIZE,
        events:       app.renderer.events,
      })
      app.stage.addChild(viewport)
      viewport
        .drag()
        .pinch()
        .wheel({ percent: 0.15, smooth: 8 })
        .decelerate({ friction: 0.94 })
        .clampZoom({ minScale: 0.05, maxScale: 30 })
      appRef.current._viewport = viewport

      const cityW = (xMax - xMin + padX * 2) * WORLD_SIZE
      const cityH = (yMax - yMin + padY * 2) * WORLD_SIZE
      const cityX = (xMin - padX) * WORLD_SIZE + cityW / 2
      const cityY = (yMin - padY) * WORLD_SIZE + cityH / 2
      viewport.fit(true, cityW, cityH)
      viewport.moveCenter(cityX, cityY)

      // ── Grid: hover detection — mouse → grid cell → district id ───
      const GRID  = 300
      const cellCounts = Array.from({ length: GRID * GRID }, () => ({}))
      points.forEach(p => {
        if (p.ct === -1) return
        const gx  = Math.min(Math.floor(p.x * GRID), GRID - 1)
        const gy  = Math.min(Math.floor(p.y * GRID), GRID - 1)
        const idx = gy * GRID + gx
        cellCounts[idx][p.ct] = (cellCounts[idx][p.ct] || 0) + 1
      })

      const gridMap = new Int16Array(GRID * GRID).fill(-1)
      cellCounts.forEach((counts, idx) => {
        let best = -1, bestCount = 0
        for (const ct in counts) {
          if (counts[ct] > bestCount) { bestCount = counts[ct]; best = parseInt(ct) }
        }
        gridMap[idx] = best
      })

      // ── District region tints — organic soft-glow atmosphere ─────
      // Draw a large soft circle at every tweet's world position, grouped
      // by district colour. Overlapping circles naturally build up brightness
      // at dense cluster centres — no grid artifacts, fully HD.
      const regionsG = new Graphics()
      const pointsByDistrict = {}
      points.forEach(p => {
        if (p.ct === -1) return
        if (!pointsByDistrict[p.ct]) pointsByDistrict[p.ct] = []
        pointsByDistrict[p.ct].push(p)
      })
      for (const ct in pointsByDistrict) {
        regionsG.beginFill(DISTRICT_COLOURS[parseInt(ct) % DISTRICT_COLOURS.length], 0.07)
        pointsByDistrict[ct].forEach(p =>
          regionsG.drawCircle(p.x * WORLD_SIZE, p.y * WORLD_SIZE, 22)
        )
        regionsG.endFill()
      }
      regionsG.alpha = 0
      viewport.addChild(regionsG)
      appRef.current._ref_regionsG = regionsG

      // ── Build connection index (parent/child lookup per tweet) ────
      const connIndex = new Map()
      if (connRaw) {
        for (let i = 0; i < connRaw.length; i += 3) {
          const fromIdx = connRaw[i], toIdx = connRaw[i + 1]
          // fromIdx replied TO toIdx → toIdx is the parent
          if (!connIndex.has(fromIdx)) connIndex.set(fromIdx, { parents: [], children: [] })
          if (!connIndex.has(toIdx))   connIndex.set(toIdx,   { parents: [], children: [] })
          connIndex.get(fromIdx).parents.push(toIdx)
          connIndex.get(toIdx).children.push(fromIdx)
        }
      }
      appRef.current._connIndex = connIndex

      // ── Standalone dots (city fabric, background noise) ────────────
      const standaloneG = new Graphics()
      standaloneG.beginFill(STANDALONE_COLOUR, 0.15)
      points.forEach(p => {
        if (p.ct === -1) standaloneG.drawCircle(p.x * WORLD_SIZE, p.y * WORLD_SIZE, 1.5)
      })
      standaloneG.endFill()
      viewport.addChild(standaloneG)

      // ── District dots — warm white + additive blend = city lights ──
      districts.forEach(d => {
        const g = new Graphics()
        g.blendMode = BLEND_MODES.ADD
        g.beginFill(0xffe8c0, 0.7)
        points.forEach(p => {
          if (p.ct === d.id) {
            const size = p.l > 10000 ? 4 : p.l > 2000 ? 3 : p.l > 500 ? 2.2 : 1.8
            g.drawCircle(p.x * WORLD_SIZE, p.y * WORLD_SIZE, size)
          }
        })
        g.endFill()
        viewport.addChild(g)
      })

      // ── Visited dots — pulsing glow, redrawn each tick ────────────
      const visitedG = new Graphics()
      visitedG.blendMode = BLEND_MODES.ADD
      viewport.addChild(visitedG)
      appRef.current._visitedG = visitedG

      // ── Reply chain — lines to/from clicked tweet ─────────────────
      const replyChainG = new Graphics()
      replyChainG.blendMode = BLEND_MODES.ADD
      replyChainG.alpha = 0
      viewport.addChild(replyChainG)
      appRef.current._replyChainG      = replyChainG
      appRef.current._replyChainTarget = 0

      // ── Events ─────────────────────────────────────────────────────
      app.stage.eventMode = 'static'
      app.stage.hitArea   = app.screen

      // District hover: grid cell lookup with debounce.
      // Fast cursor sweeps don't trigger panel updates — only pausing
      // over a district for 200ms commits the change. Eliminates flicker.
      let hoverTimer = null
      app.stage.on('pointermove', (e) => {
        const world = viewport.toWorld(e.global.x, e.global.y)
        const gx = Math.floor((world.x / WORLD_SIZE) * GRID)
        const gy = Math.floor((world.y / WORLD_SIZE) * GRID)

        const ct = (gx >= 0 && gx < GRID && gy >= 0 && gy < GRID)
          ? gridMap[gy * GRID + gx]
          : -1

        if (ct === lastHoveredIdRef.current) return  // no change

        clearTimeout(hoverTimer)
        hoverTimer = setTimeout(() => {
          lastHoveredIdRef.current = ct
          if (ct === -1) {
            setHoveredDistrict(null)
            return
          }
          const dData = districtsById[ct]
          const info  = DISTRICT_INFO[ct] || { name: `District ${ct}`, desc: '' }
          const color = DISTRICT_COLOURS[ct % DISTRICT_COLOURS.length]
          setHoveredDistrict({ ct, color, ...dData, ...info })
        }, 200)
      })

      // Clear panel when cursor leaves the canvas entirely
      app.stage.on('pointerout', () => {
        clearTimeout(hoverTimer)
        lastHoveredIdRef.current = -1
        setHoveredDistrict(null)
      })

      // Click: find nearest tweet within radius
      const worldPoints = points.map((p, i) => ({ wx: p.x * WORLD_SIZE, wy: p.y * WORLD_SIZE, i }))
      let lastEmptyClickTime = 0, lastEmptyClickWorld = null
      app.stage.on('pointerdown', async (e) => {
        const world  = viewport.toWorld(e.global.x, e.global.y)
        // 30 screen-pixel hit radius at any zoom level
        const RADIUS = 30 / viewport.scale.x
        let nearest = null, nearestDist = Infinity

        for (const wp of worldPoints) {
          const dx = wp.wx - world.x
          const dy = wp.wy - world.y
          const d  = dx * dx + dy * dy
          if (d < nearestDist && d < RADIUS * RADIUS) { nearestDist = d; nearest = wp }
        }

        if (!nearest) {
          const now = Date.now()
          // Only allow double-click zoom when at overview scale — at high zoom
          // it conflicts with precise tweet clicking (user misses, retries quickly)
          const canZoom = viewport.scale.x < 1.5
          const isDoubleClick = canZoom && lastEmptyClickWorld &&
            (now - lastEmptyClickTime) < 350 &&
            Math.abs(world.x - lastEmptyClickWorld.x) < 100 &&
            Math.abs(world.y - lastEmptyClickWorld.y) < 100

          if (isDoubleClick) {
            const gx = Math.min(Math.floor((world.x / WORLD_SIZE) * GRID), GRID - 1)
            const gy = Math.min(Math.floor((world.y / WORLD_SIZE) * GRID), GRID - 1)
            const ct = (gx >= 0 && gy >= 0) ? gridMap[gy * GRID + gx] : -1
            const d  = ct !== -1 ? districtsById[ct] : null
            if (d) {
              viewport.animate({
                position: { x: d.cx * WORLD_SIZE, y: d.cy * WORLD_SIZE },
                scale: 2.0,
                time: 800,
                ease: 'easeInOutSine',
              })
            }
            lastEmptyClickTime = 0; lastEmptyClickWorld = null
          } else {
            lastEmptyClickTime  = now
            lastEmptyClickWorld = { x: world.x, y: world.y }
            setSelectedTweet(null)
            if (appRef.current._replyChainG) appRef.current._replyChainTarget = 0
          }
          return
        }
        const p = points[nearest.i]

        // Draw reply chain immediately (sync) — before any async tweet fetch
        // so there's no gap where a misclick could reset the target to 0
        const rcg = appRef.current._replyChainG
        if (rcg) {
          rcg.clear()
          const idx   = nearest.i
          const entry = appRef.current._connIndex?.get(idx)
          if (entry) {
            const self = worldPoints[idx]
            // Parent lines — bright warm white, thick
            rcg.lineStyle(4, 0xfff8e0, 1.0)
            entry.parents.forEach(toIdx => {
              const to = worldPoints[toIdx]
              if (to) { rcg.moveTo(self.wx, self.wy); rcg.lineTo(to.wx, to.wy) }
            })
            // Children lines — amber, solid
            rcg.lineStyle(3, 0xf0b040, 0.9)
            entry.children.slice(0, 30).forEach(fromIdx => {
              const from = worldPoints[fromIdx]
              if (from) { rcg.moveTo(from.wx, from.wy); rcg.lineTo(self.wx, self.wy) }
            })
            // Glow dot on the clicked tweet itself
            rcg.lineStyle(0)
            rcg.beginFill(0xffffff, 1.0)
            rcg.drawCircle(self.wx, self.wy, 8)
            rcg.endFill()
            // Glow dots on parent endpoints
            rcg.beginFill(0xfff8e0, 0.95)
            entry.parents.forEach(toIdx => {
              const to = worldPoints[toIdx]
              if (to) rcg.drawCircle(to.wx, to.wy, 6)
            })
            rcg.endFill()
            // Glow dots on child endpoints
            rcg.beginFill(0xf0b040, 0.85)
            entry.children.slice(0, 30).forEach(fromIdx => {
              const from = worldPoints[fromIdx]
              if (from) rcg.drawCircle(from.wx, from.wy, 5)
            })
            rcg.endFill()
          }
          appRef.current._replyChainTarget = entry ? 1 : 0
        }

        // Load tweet text (deferred until first click)
        if (!appRef.current._tweetsCache) {
          setStatus('Loading tweet text...')
          appRef.current._tweetsCache = await fetch('/tweets.json').then(r => r.json())
          setStatus('')
        }

        const tweet = appRef.current._tweetsCache[p.id]
        if (tweet) {
          const dData = p.ct !== -1 ? districtsById[p.ct] : null
          const info  = DISTRICT_INFO[p.ct] || { name: `District ${p.ct}`, desc: '' }
          const color = DISTRICT_COLOURS[p.ct >= 0 ? p.ct % DISTRICT_COLOURS.length : 0]
          const entry = { id: p.id, text: tweet.text, date: tweet.date, likes: tweet.likes,
                          ct: p.ct, color, name: info.name }

          setSelectedTweet({ ...tweet, id: p.id })
          if (p.ct !== -1) setPinnedDistrict({ ct: p.ct, color, ...dData, ...info })

          // Mark visited (glowing dot)
          visitedIdsRef.current.add(p.id)
          try { localStorage.setItem('threadthulhu_visited', JSON.stringify([...visitedIdsRef.current])) } catch (e) {}

          // Add to explorer's trail (prepend, cap at 50)
          setTrail(prev => {
            const next = [entry, ...prev.filter(e => e.id !== p.id)].slice(0, 50)
            try { localStorage.setItem('threadthulhu_trail', JSON.stringify(next)) } catch (e) {}
            return next
          })
        }
      })

      // ── Ticker: road + region fades + visited pulse ────────────────
      app.ticker.add(() => {
        const scale = viewport.scale.x
        const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v))

        // District tints: full colour at city overview, fade OUT as you zoom in
        // Visible at scale < 0.10, fully gone by scale 0.30
        if (appRef.current?._ref_regionsG)
          appRef.current._ref_regionsG.alpha = clamp((0.30 - scale) / 0.20, 0, 1)

        // Reply chain: smooth fade toward target
        const rcg = appRef.current?._replyChainG
        if (rcg) rcg.alpha += (appRef.current._replyChainTarget - rcg.alpha) * 0.08

        // Pulse visited dots via Pixi visitedG
        const pulse = 1 + 0.5 * Math.sin(Date.now() * 0.0025)
        const vg = appRef.current?._visitedG
        if (vg) {
          vg.clear()
          if (visitedIdsRef.current.size > 0) {
            vg.beginFill(0xfffce0, 0.95)
            for (const id of visitedIdsRef.current) {
              const pt = appRef.current._pointsById?.[id]
              if (pt) vg.drawCircle(pt.wx, pt.wy, pt.size * pulse * 4)
            }
            vg.endFill()
          }
        }
      })

      setStatus('')
    }

    init().catch(err => {
      console.error(err)
      setStatus('Error loading city data. Run pipeline/06_export_frontend_data.py first.')
    })

    return () => { if (appRef.current) { appRef.current.destroy(true); appRef.current = null } }
  }, [])

  // Panel to display: pinned (from tweet click) takes priority over hovered
  const displayDistrict = pinnedDistrict || hoveredDistrict
  // If pinned and hovering a different district, show "now in" indicator
  const nowInDistrict = pinnedDistrict && hoveredDistrict && hoveredDistrict.ct !== pinnedDistrict.ct
    ? hoveredDistrict : null

  const accentCSS = displayDistrict ? hexToCSS(displayDistrict.color) : '#fff'

  const handleExplore = async (ct) => {
    const ids = tweetsByDistrictRef.current[ct]
    if (!ids?.length) return
    const randomId = ids[Math.floor(Math.random() * ids.length)]
    if (!appRef.current._tweetsCache) {
      setStatus('Loading tweet text...')
      appRef.current._tweetsCache = await fetch('/tweets.json').then(r => r.json())
      setStatus('')
    }
    const tweet = appRef.current._tweetsCache[randomId]
    if (tweet) {
      setSelectedTweet({ ...tweet, id: randomId })
      setPinnedDistrict(displayDistrict)
    }
  }

  const closeTweet = () => { setSelectedTweet(null); setPinnedDistrict(null) }

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

      {/* Loading */}
      {status && (
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%,-50%)',
          color: '#444', fontFamily: "'Cinzel', serif", fontSize: 12, letterSpacing: 3,
          textTransform: 'uppercase',
        }}>
          {status}
        </div>
      )}

      {/* Title — top left */}
      <div style={{
        position: 'absolute', top: 24, left: 28,
        pointerEvents: 'none',
      }}>
        <div style={{
          fontFamily: "'Cinzel', serif", fontSize: 15, fontWeight: 600,
          letterSpacing: 4, textTransform: 'uppercase', color: '#ede8df',
          textShadow: '0 0 12px rgba(255,232,192,0.25)',
        }}>
          Threadthulhu
        </div>
        <div style={{
          fontFamily: "'Cinzel', serif", fontSize: 9, letterSpacing: 5,
          textTransform: 'uppercase', marginTop: 4,
          color: '#fff5e0',
          textShadow: '0 0 4px rgba(255,255,255,1), 0 0 10px rgba(255,232,192,1), 0 0 25px rgba(255,180,80,0.95), 0 0 55px rgba(255,120,40,0.7), 0 0 90px rgba(255,80,20,0.35)',
        }}>
          A cartography of @visakanv
        </div>
      </div>

      {/* Hint — bottom left */}
      <div style={{
        position: 'absolute', bottom: 24, left: 28,
        fontFamily: "'Cinzel', serif", fontSize: 11, letterSpacing: 3,
        textTransform: 'uppercase', color: '#888', pointerEvents: 'none',
        textShadow: '0 0 8px rgba(255,220,160,0.2)',
      }}>
        hover to explore · click a light to read
      </div>

      {/* Explorer's Trail — full-height right sidebar */}
      <div style={{
        position: 'absolute', top: 0, right: 0, bottom: 0, width: 300,
        display: 'flex', flexDirection: 'column',
        pointerEvents: 'none',
      }}>
        {/* Scrollable list — fills all space above button */}
        {trailOpen && (
          <div style={{
            flex: 1, overflowY: 'auto',
            background: 'rgba(6,6,12,0.97)',
            borderLeft: '1px solid rgba(255,220,140,0.2)',
            pointerEvents: 'all',
          }}>
            <div style={{
              padding: '20px 18px 10px',
              fontFamily: "'Cinzel', serif", fontSize: 10,
              letterSpacing: 4, textTransform: 'uppercase',
              color: '#e8d5a8',
              textShadow: '0 0 8px rgba(255,210,120,0.6)',
              borderBottom: '1px solid rgba(255,220,140,0.12)',
            }}>
              Explorer's Trail
            </div>
            {trail.length === 0 && (
              <div style={{ padding: '20px 18px', fontFamily: "'Spectral', serif",
                fontSize: 14, fontStyle: 'italic', color: '#777' }}>
                No threads visited yet.
              </div>
            )}
            {trail.map((entry) => {
              const c = hexToCSS(entry.color ?? DISTRICT_COLOURS[0])
              return (
                <div
                  key={entry.id}
                  onClick={() => {
                    setSelectedTweet({ text: entry.text, date: entry.date, likes: entry.likes, id: entry.id })
                    setPinnedDistrict(null)
                  }}
                  style={{
                    padding: '14px 16px', cursor: 'pointer',
                    borderTop: '1px solid rgba(255,255,255,0.07)',
                    borderLeft: `3px solid ${c}`,
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <div style={{
                    fontFamily: "'Cinzel', serif", fontSize: 9,
                    letterSpacing: 3, textTransform: 'uppercase',
                    color: c, marginBottom: 6,
                    textShadow: `0 0 10px ${c}bb`,
                  }}>
                    {entry.name}
                  </div>
                  <div style={{
                    fontFamily: "'Spectral', serif", fontSize: 13,
                    fontStyle: 'italic', color: '#ccc', lineHeight: 1.55,
                    overflow: 'hidden', display: '-webkit-box',
                    WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                  }}>
                    {entry.text}
                  </div>
                  <div style={{
                    fontFamily: "'Cinzel', serif", fontSize: 9,
                    color: '#777', marginTop: 6, letterSpacing: 1,
                  }}>
                    {entry.date?.slice(0, 10)}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Toggle tab — always visible at bottom */}
        <button
          onClick={() => setTrailOpen(o => !o)}
          style={{
            pointerEvents: 'all',
            background: 'rgba(6,6,12,0.97)',
            cursor: 'pointer',
            border: '1px solid rgba(255,220,140,0.35)',
            borderRight: 'none',
            color: '#e8d5a8',
            fontFamily: "'Cinzel', serif", fontSize: 11,
            letterSpacing: 4, textTransform: 'uppercase',
            padding: '12px 18px', textAlign: 'left',
            textShadow: '0 0 10px rgba(255,210,120,0.8), 0 0 25px rgba(255,180,80,0.5)',
            boxShadow: '0 0 20px rgba(255,200,100,0.15)',
          }}
        >
          {trailOpen ? '↓ close trail' : `↑ explorer's trail${trail.length ? `  ·  ${trail.length}` : ''}`}
        </button>
      </div>

      {/* "Now entering" toast — bottom center, appears when drifting into a new district */}
      {nowInDistrict && (
        <div style={{
          position: 'absolute', top: 24, left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(4, 4, 10, 0.93)',
          borderTop: `2px solid ${hexToCSS(nowInDistrict.color)}`,
          border: `1px solid ${hexToCSS(nowInDistrict.color)}44`,
          borderTopColor: hexToCSS(nowInDistrict.color),
          padding: '9px 28px',
          fontFamily: "'Cinzel', serif", fontSize: 12,
          letterSpacing: 5, textTransform: 'uppercase',
          color: hexToCSS(nowInDistrict.color),
          textShadow: `0 0 14px ${hexToCSS(nowInDistrict.color)}bb, 0 0 30px ${hexToCSS(nowInDistrict.color)}44`,
          pointerEvents: 'none', whiteSpace: 'nowrap',
        }}>
          now entering · {nowInDistrict.name}
        </div>
      )}

      {/* District panel — left side ───────────────────────────────── */}
      {displayDistrict && (
        <div style={{
          position:    'absolute', left: 24, top: '50%',
          transform:   'translateY(-50%)', width: 272,
          background:  'rgba(5, 5, 10, 0.94)',
          borderTop:   `2px solid ${accentCSS}`,
          border:      `1px solid rgba(255,255,255,0.08)`,
          borderTopColor: accentCSS,
          padding:     '18px 20px 16px',
        }}>

          {/* Census label */}
          <div style={{
            fontFamily: "'Cinzel', serif", fontSize: 10,
            letterSpacing: 4, textTransform: 'uppercase',
            color: accentCSS, marginBottom: 10,
            textShadow: `0 0 8px ${accentCSS}99`,
          }}>
            District Record
          </div>

          {/* Name */}
          <div style={{
            fontFamily: "'Cinzel', serif", fontSize: 18, fontWeight: 500,
            letterSpacing: 2, textTransform: 'uppercase',
            color: '#f5f0e8', lineHeight: 1.3, marginBottom: 10,
            textShadow: `0 0 10px ${accentCSS}cc, 0 0 30px ${accentCSS}55`,
          }}>
            {displayDistrict.name}
          </div>

          {/* Description */}
          <div style={{
            fontFamily: "'Spectral', Georgia, serif", fontSize: 14,
            fontStyle: 'italic', color: '#c0bbb3', lineHeight: 1.65,
            marginBottom: 14, paddingBottom: 12,
            borderBottom: '1px solid rgba(255,255,255,0.08)',
          }}>
            {displayDistrict.desc}
          </div>

          {/* Stats */}
          <div style={{
            fontFamily: "'Spectral', Georgia, serif", fontSize: 13,
            color: '#9a9590', lineHeight: 2.0, fontVariantNumeric: 'tabular-nums',
          }}>
            <div>{displayDistrict.tweet_count?.toLocaleString()} threads</div>
            <div>Est. {displayDistrict.year_range}</div>
            <div>♥ {Math.round(displayDistrict.avg_likes)} avg · {displayDistrict.max_likes?.toLocaleString()} peak</div>
          </div>

          {/* Keywords */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginTop: 12, marginBottom: 14 }}>
            {displayDistrict.keywords?.slice(0, 5).map(kw => (
              <span key={kw} style={{
                fontFamily: "'Cinzel', serif", fontSize: 10,
                letterSpacing: 2, textTransform: 'uppercase',
                padding: '4px 10px',
                border: `1px solid ${accentCSS}77`,
                color: accentCSS + 'ee',
                textShadow: `0 0 8px ${accentCSS}99`,
              }}>
                {kw}
              </span>
            ))}
          </div>

          {/* Top tweet */}
          {displayDistrict.top_tweet && (
            <div style={{
              fontFamily: "'Spectral', Georgia, serif", fontSize: 13,
              fontStyle: 'italic', color: '#8a8580', lineHeight: 1.6,
              borderTop: '1px solid rgba(255,255,255,0.07)', paddingTop: 10,
              marginBottom: 14,
            }}>
              "{displayDistrict.top_tweet.slice(0, 120)}{displayDistrict.top_tweet.length > 120 ? '…' : ''}"
            </div>
          )}

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => {
                const vp = appRef.current?._viewport
                const d  = displayDistrict
                if (vp && d.cx != null) vp.animate({
                  position: { x: d.cx * WORLD_SIZE, y: d.cy * WORLD_SIZE },
                  scale: 2.5, time: 900, ease: 'easeInOutSine',
                })
              }}
              style={{
                background: 'none', cursor: 'pointer',
                border: `1px solid ${accentCSS}66`,
                color: accentCSS,
                fontFamily: "'Cinzel', serif", fontSize: 10,
                letterSpacing: 3, textTransform: 'uppercase',
                padding: '8px 12px', flex: 1,
                textShadow: `0 0 10px ${accentCSS}88`,
              }}
            >
              Fly in ↗
            </button>
            <button
              onClick={() => handleExplore(displayDistrict.ct)}
              style={{
                background: 'none', cursor: 'pointer',
                border: `1px solid ${accentCSS}66`,
                color: accentCSS,
                fontFamily: "'Cinzel', serif", fontSize: 10,
                letterSpacing: 3, textTransform: 'uppercase',
                padding: '8px 12px', flex: 2,
                textShadow: `0 0 10px ${accentCSS}88`,
              }}
            >
              Explore a thread →
            </button>
          </div>

        </div>
      )}

      {/* Tweet panel — bottom center */}
      {selectedTweet && (
        <div style={{
          position:  'absolute', bottom: 0, left: '50%',
          transform: 'translateX(-50%)',
          width: 'min(640px, calc(100vw - 340px))',
          background:'rgba(5, 5, 10, 0.96)',
          borderTop: '2px solid rgba(255,232,192,0.35)',
          borderLeft: '1px solid rgba(255,255,255,0.07)',
          borderRight:'1px solid rgba(255,255,255,0.07)',
          padding:   '20px 28px 20px',
          fontFamily:"'Spectral', Georgia, serif",
          color:     '#ccc',
        }}>
          <div
            onClick={closeTweet}
            style={{
              position: 'absolute', top: 14, right: 18,
              color: '#777', cursor: 'pointer', fontSize: 16,
              fontFamily: 'sans-serif', lineHeight: 1,
            }}
          >✕</div>

          {/* Tweet text */}
          <div style={{ fontSize: 15, lineHeight: 1.7, marginBottom: 14, color: '#c8c3bb' }}>
            {selectedTweet.text.split(/(https?:\/\/\S+)/g).map((part, i) =>
              part.match(/^https?:\/\//) ? (
                <a key={i} href={part} target="_blank" rel="noreferrer"
                  style={{ color: '#5a7a9a', wordBreak: 'break-all' }}>
                  {part}
                </a>
              ) : part
            )}
          </div>

          {/* Meta */}
          <div style={{
            fontSize: 12, color: '#9a9590', display: 'flex', gap: 16,
            fontFamily: "'Cinzel', serif", letterSpacing: 1,
            borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 10,
          }}>
            <span>{selectedTweet.date?.slice(0, 10)}</span>
            <span>♥ {selectedTweet.likes?.toLocaleString()}</span>
          </div>

          <a
            href={`https://x.com/visakanv/status/${selectedTweet.id}`}
            target="_blank" rel="noreferrer"
            style={{
              fontSize: 11, color: '#6a8aaa', marginTop: 10, display: 'block',
              fontFamily: "'Cinzel', serif", letterSpacing: 2, textTransform: 'uppercase',
            }}
          >
            View on X →
          </a>
        </div>
      )}
    </div>
  )
}
