import { useEffect, useRef, useState } from 'react'
import { Application, Graphics, Container, Text, TextStyle } from 'pixi.js'
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

const STANDALONE_COLOUR = 0x444444  // slightly brighter — they form the city body
const WORLD_SIZE        = 8000

export default function App() {
  const containerRef  = useRef(null)
  const appRef        = useRef(null)
  const pointsDataRef = useRef(null)  // raw points array, for click lookup
  const [status, setStatus]         = useState('Loading city data...')
  const [selectedTweet, setSelectedTweet] = useState(null)  // clicked tweet

  useEffect(() => {
    let app, viewport

    async function init() {
      // ── Load data ─────────────────────────────────────────────────
      setStatus('Loading points...')
      const [pointsRes, districtsRes] = await Promise.all([
        fetch('/points.json'),
        fetch('/districts.json'),
      ])
      const points    = await pointsRes.json()
      const districts = await districtsRes.json()
      pointsDataRef.current = points
      setStatus('Rendering city...')

      // ── Compute tight bounding box to fit the city properly ───────
      // The data is normalised 0-1 but the city doesn't fill the whole space.
      // Find the actual data bounds and add a small margin.
      let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity
      points.forEach(p => {
        if (p.x < xMin) xMin = p.x
        if (p.x > xMax) xMax = p.x
        if (p.y < yMin) yMin = p.y
        if (p.y > yMax) yMax = p.y
      })
      const dataX = { min: xMin, max: xMax }
      const dataY = { min: yMin, max: yMax }
      const padX   = (dataX.max - dataX.min) * 0.05
      const padY   = (dataY.max - dataY.min) * 0.05

      // ── Pixi application ──────────────────────────────────────────
      app = new Application({
        width:           containerRef.current.clientWidth,
        height:          containerRef.current.clientHeight,
        backgroundColor: 0x0d0d0d,
        antialias:       false,
        resolution:      window.devicePixelRatio || 1,
        autoDensity:     true,
      })
      containerRef.current.appendChild(app.view)
      appRef.current = app

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
        .wheel()
        .decelerate({ friction: 0.94 })
        .clampZoom({ minScale: 0.05, maxScale: 30 })

      // Fit view tightly to the actual data extent
      const cityW = (dataX.max - dataX.min + padX * 2) * WORLD_SIZE
      const cityH = (dataY.max - dataY.min + padY * 2) * WORLD_SIZE
      const cityX = (dataX.min - padX) * WORLD_SIZE + cityW / 2
      const cityY = (dataY.min - padY) * WORLD_SIZE + cityH / 2
      viewport.fit(true, cityW, cityH)
      viewport.moveCenter(cityX, cityY)

      // ── Draw standalone points (background city fabric) ───────────
      const standaloneG = new Graphics()
      standaloneG.beginFill(STANDALONE_COLOUR, 0.5)
      points.forEach(p => {
        if (p.ct === -1) {
          standaloneG.drawCircle(p.x * WORLD_SIZE, p.y * WORLD_SIZE, 1.5)
        }
      })
      standaloneG.endFill()
      viewport.addChild(standaloneG)

      // ── Draw district points ──────────────────────────────────────
      // One Graphics object per district = one draw call per colour = fast
      districts.forEach(d => {
        const g      = new Graphics()
        const colour = DISTRICT_COLOURS[d.id % DISTRICT_COLOURS.length]
        g.beginFill(colour, 0.8)
        points.forEach(p => {
          if (p.ct === d.id) {
            const size = p.l > 10000 ? 4 : p.l > 2000 ? 3 : p.l > 500 ? 2.2 : 1.8
            g.drawCircle(p.x * WORLD_SIZE, p.y * WORLD_SIZE, size)
          }
        })
        g.endFill()
        viewport.addChild(g)
      })

      // ── District labels ───────────────────────────────────────────
      // Labels are scaled inversely to viewport zoom so they stay
      // a consistent on-screen size regardless of zoom level.
      const labelsContainer = new Container()
      viewport.addChild(labelsContainer)

      const labelStyle = new TextStyle({
        fontFamily: 'Georgia, serif',
        fontSize:   18,           // large in world space — scaled down at runtime
        fill:       0xffffff,
        letterSpacing: 1,
      })

      districts.forEach(d => {
        const label = new Text(d.keywords.slice(0, 2).join('  ·  '), labelStyle)
        label.x     = d.cx * WORLD_SIZE
        label.y     = d.cy * WORLD_SIZE
        label.anchor.set(0.5)
        labelsContainer.addChild(label)
      })

      // ── Click to select nearest tweet ────────────────────────────
      // Build a simple spatial index: array of {x, y, idx} in world coords
      const worldPoints = points.map((p, i) => ({
        wx: p.x * WORLD_SIZE,
        wy: p.y * WORLD_SIZE,
        i,
      }))

      app.stage.eventMode = 'static'
      app.stage.hitArea   = app.screen

      app.stage.on('pointerdown', async (e) => {
        // Convert screen coords → world coords
        const world = viewport.toWorld(e.global.x, e.global.y)

        // Find nearest point within 20px world-space radius
        const RADIUS = 20 / viewport.scale.x  // adjust for zoom
        let nearest = null
        let nearestDist = Infinity

        for (const wp of worldPoints) {
          const dx = wp.wx - world.x
          const dy = wp.wy - world.y
          const d  = dx * dx + dy * dy
          if (d < nearestDist && d < RADIUS * RADIUS) {
            nearestDist = d
            nearest     = wp
          }
        }

        if (!nearest) {
          setSelectedTweet(null)
          return
        }

        const p = points[nearest.i]

        // Lazy-load tweet text from tweets.json
        if (!appRef.current._tweetsCache) {
          setStatus('Loading tweet text...')
          const res = await fetch('/tweets.json')
          appRef.current._tweetsCache = await res.json()
          setStatus('')
        }

        const tweet = appRef.current._tweetsCache[p.id]
        if (tweet) {
          setSelectedTweet({ ...tweet, id: p.id })
        }
      })

      // ── Ticker: scale labels + fade by zoom ───────────────────────
      app.ticker.add(() => {
        const scale = viewport.scale.x

        // Keep labels a consistent on-screen size
        labelsContainer.children.forEach(label => {
          label.scale.set(1 / scale)
        })

        // Fade labels in — visible from initial city view onwards
        labelsContainer.alpha = Math.min(1, Math.max(0, (scale - 0.03) / 0.04))
      })

      setStatus('')
    }

    init().catch(err => {
      console.error(err)
      setStatus('Error loading city data. Run pipeline/06_export_frontend_data.py first.')
    })

    return () => {
      if (appRef.current) {
        appRef.current.destroy(true)
        appRef.current = null
      }
    }
  }, [])

  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <div ref={containerRef} style={{ width: '100%', height: '100%' }} />

      {/* Loading status */}
      {status && (
        <div style={{
          position: 'absolute', top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)',
          color: '#666', fontFamily: 'Georgia, serif', fontSize: 14,
        }}>
          {status}
        </div>
      )}

      {/* Title */}
      <div style={{
        position: 'absolute', top: 20, left: 24,
        color: '#fff', fontFamily: 'Georgia, serif',
        pointerEvents: 'none',
      }}>
        <div style={{ fontSize: 18, fontWeight: 'bold', letterSpacing: 1 }}>
          Threadthulhu City
        </div>
        <div style={{ fontSize: 11, color: '#555', marginTop: 2 }}>
          @visakanv · scroll to zoom · drag to explore · click a dot to read
        </div>
      </div>

      {/* Tweet panel — anchored top-right, always visible regardless of zoom */}
      {selectedTweet && (
        <div style={{
          position:     'absolute',
          top:          20,
          right:        24,
          width:        340,
          maxHeight:    'calc(100vh - 40px)',
          overflowY:    'auto',
          background:   'rgba(10,10,10,0.95)',
          border:       '1px solid #333',
          borderRadius: 6,
          padding:      '16px 18px',
          fontFamily:   'Georgia, serif',
          color:        '#ddd',
        }}>
          {/* Close button */}
          <div
            onClick={() => setSelectedTweet(null)}
            style={{
              position: 'absolute', top: 10, right: 14,
              color: '#555', cursor: 'pointer', fontSize: 16,
            }}
          >✕</div>

          {/* Tweet text — URLs made clickable */}
          <div style={{ fontSize: 14, lineHeight: 1.6, marginBottom: 12 }}>
            {selectedTweet.text.split(/(https?:\/\/\S+)/g).map((part, i) =>
              part.match(/^https?:\/\//) ? (
                <a key={i} href={part} target="_blank" rel="noreferrer"
                  style={{ color: '#4e79a7', wordBreak: 'break-all' }}>
                  {part}
                </a>
              ) : part
            )}
          </div>

          {/* Metadata */}
          <div style={{ fontSize: 11, color: '#555', display: 'flex', gap: 16 }}>
            <span>{selectedTweet.date?.slice(0, 10)}</span>
            <span>♥ {selectedTweet.likes?.toLocaleString()}</span>
          </div>

          {/* Link to original tweet */}
          <a
            href={`https://x.com/visakanv/status/${selectedTweet.id}`}
            target="_blank"
            rel="noreferrer"
            style={{ fontSize: 11, color: '#4e79a7', marginTop: 8, display: 'block' }}
          >
            View on X →
          </a>
        </div>
      )}
    </div>
  )
}
