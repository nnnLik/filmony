import { useEffect, useRef } from 'react'

const SEGMENTS = 56
const FFT_SIZE = 512
const CANVAS_CSS_PX_DEFAULT = 118
const CANVAS_CSS_PX_COMPACT = 104

type RGB = { r: number; g: number; b: number }

/** Бирюзовый / янтарный — совпадают с палитрой filmony-theme */
const FILM_MINT: RGB = { r: 94, g: 234, b: 212 }
const FILM_AMBER: RGB = { r: 232, g: 184, b: 109 }

function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
    return false
  }
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function pickAudioContext(): typeof AudioContext {
  const w = window as unknown as { webkitAudioContext?: typeof AudioContext }
  return w.webkitAudioContext ?? AudioContext
}

function tryCaptureStreamFromAudio(el: HTMLAudioElement): MediaStream | null {
  const extended = el as HTMLMediaElement & { captureStream?: () => MediaStream }
  const cap = extended.captureStream
  if (typeof cap !== 'function') {
    return null
  }
  try {
    const stream = cap.call(extended)
    return stream instanceof MediaStream ? stream : null
  } catch {
    return null
  }
}

function hexToRgb(hex: string): RGB | null {
  const s = hex.trim()
  const m = /^#?([0-9a-f]{6})$/i.exec(s)
  if (m == null) return null
  const n = Number.parseInt(m[1], 16)
  return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 }
}

function lerpRgb(a: RGB, b: RGB, t: number): RGB {
  const u = Math.min(1, Math.max(0, t))
  return {
    r: Math.round(a.r + (b.r - a.r) * u),
    g: Math.round(a.g + (b.g - a.g) * u),
    b: Math.round(a.b + (b.b - a.b) * u),
  }
}

function rgba(c: RGB, alpha: number): string {
  return `rgba(${c.r},${c.g},${c.b},${alpha})`
}

function polar(cx: number, cy: number, r: number, th: number): [number, number] {
  return [cx + Math.cos(th) * r, cy + Math.sin(th) * r]
}

type MovieCardRatingAudioVisualizerProps = {
  audio: HTMLAudioElement | null
  audioUrl: string
  /** Цвет кольца оценки (hex), смешивается в градиент */
  ringColor: string
  /** Меньший холст — для компактного оверлея на постере рядом с оценкой */
  compact?: boolean
}

/**
 * Круговая волна по спектру вокруг оценки: сегменты с радиальным градиентом mint → amber по силе.
 * Работает только при воспроизведении; при паузе canvas пустой.
 */
export function MovieCardRatingAudioVisualizer({
  audio,
  audioUrl,
  ringColor,
  compact = false,
}: MovieCardRatingAudioVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const canvasCssPx = compact ? CANVAS_CSS_PX_COMPACT : CANVAS_CSS_PX_DEFAULT

  useEffect(() => {
    const canvas = canvasRef.current
    if (canvas == null || audio == null || prefersReducedMotion()) {
      return
    }

    const dpr = window.devicePixelRatio ?? 1
    const w = canvasCssPx
    canvas.width = Math.round(w * dpr)
    canvas.height = Math.round(w * dpr)
    canvas.style.width = `${w}px`
    canvas.style.height = `${w}px`
    const ctx2d = canvas.getContext('2d')
    if (ctx2d != null) {
      ctx2d.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
  }, [audio, audioUrl, canvasCssPx])

  useEffect(() => {
    if (audio == null || prefersReducedMotion()) {
      return
    }

    const canvas = canvasRef.current
    if (canvas == null) return

    const ringRgb = hexToRgb(ringColor) ?? FILM_MINT
      const geomScale = canvasCssPx / CANVAS_CSS_PX_DEFAULT
    const freq = new Uint8Array(FFT_SIZE / 2)
    const raw = new Float32Array(SEGMENTS).fill(0)
    const smooth = new Float32Array(SEGMENTS).fill(0)
    const blurred = new Float32Array(SEGMENTS).fill(0)

    let rafId = 0
    let audioCtx: AudioContext | null = null
    let analyser: AnalyserNode | null = null
    let graphBuilt = false

    const stopRaf = () => {
      if (rafId !== 0) {
        cancelAnimationFrame(rafId)
        rafId = 0
      }
    }

    const clearCanvas = () => {
      const g = canvas.getContext('2d')
      if (g != null) {
        g.clearRect(0, 0, canvasCssPx, canvasCssPx)
      }
    }

    const buildGraph = async (): Promise<boolean> => {
      if (graphBuilt && audioCtx != null && analyser != null) {
        await audioCtx.resume().catch(() => {})
        return true
      }
      try {
        const AC = pickAudioContext()
        const ctx = new AC()
        const an = ctx.createAnalyser()
        an.fftSize = FFT_SIZE
        an.smoothingTimeConstant = 0.58

        let routed = false
        const stream = tryCaptureStreamFromAudio(audio)
        if (stream != null) {
          try {
            const ms = ctx.createMediaStreamSource(stream)
            ms.connect(an)
            routed = true
          } catch {
            routed = false
          }
        }
        if (!routed) {
          const source = ctx.createMediaElementSource(audio)
          source.connect(an)
          an.connect(ctx.destination)
        }

        audioCtx = ctx
        analyser = an
        graphBuilt = true
        await ctx.resume().catch(() => {})
        return true
      } catch {
        graphBuilt = false
        analyser = null
        return false
      }
    }

    const draw = () => {
      const g = canvas.getContext('2d')
      if (g == null) {
        return
      }
      if (audio.paused || analyser == null || audioCtx == null) {
        return
      }

      analyser.getByteFrequencyData(freq)
      const cx = canvasCssPx / 2
      const cy = canvasCssPx / 2
      const bufLen = freq.length
      const nyquist = audioCtx.sampleRate * 0.5
      /** Лог-полосы: иначе линейный маппинг бинов FFT даёт «пустой» сектор круга там, где высокие частоты почти всегда тише в миксе. */
      const logFLo = Math.log(35)
      const logFHi = Math.log(Math.min(16_000, nyquist * 0.95))

      for (let i = 0; i < SEGMENTS; i += 1) {
        const u0 = i / SEGMENTS
        const u1 = (i + 1) / SEGMENTS
        const f0 = Math.exp(logFLo + u0 * (logFHi - logFLo))
        const f1 = Math.exp(logFLo + u1 * (logFHi - logFLo))
        const k0 = Math.min(bufLen - 1, Math.max(0, Math.floor((f0 * bufLen) / nyquist)))
        const k1 = Math.min(bufLen, Math.max(k0 + 1, Math.ceil((f1 * bufLen) / nyquist)))
        let sum = 0
        for (let j = k0; j < k1; j += 1) {
          sum += freq[j] ?? 0
        }
        const span = Math.max(1, k1 - k0)
        raw[i] = sum / span / 255
      }

      for (let i = 0; i < SEGMENTS; i += 1) {
        smooth[i] = smooth[i] * 0.22 + raw[i] * 0.78
      }

      for (let i = 0; i < SEGMENTS; i += 1) {
        const p = smooth[(i - 1 + SEGMENTS) % SEGMENTS]
        const q = smooth[i]
        const r = smooth[(i + 1) % SEGMENTS]
        blurred[i] = p * 0.18 + q * 0.64 + r * 0.18
      }

      let mean = 0
      for (let i = 0; i < SEGMENTS; i += 1) {
        mean += blurred[i]
      }
      mean /= SEGMENTS

      g.clearRect(0, 0, canvasCssPx, canvasCssPx)

      const renderInset = compact ? 7 : 9
      const renderRadius = Math.max(24, canvasCssPx / 2 - renderInset)
      const rInner = renderRadius * 0.56
      const rBase = renderRadius * 0.74
      const amp = renderRadius * 0.22
      const thOff = -Math.PI / 2

      for (let i = 0; i < SEGMENTS; i += 1) {
        const th0 = thOff + (i / SEGMENTS) * Math.PI * 2
        const th1 = thOff + ((i + 1) / SEGMENTS) * Math.PI * 2
        const e0 = blurred[i]
        const e1 = blurred[(i + 1) % SEGMENTS]
        const em = Math.min(1, (e0 + e1) * 0.5 * 1.12 + mean * 0.15)
        const ro0 = rBase + e0 * amp
        const ro1 = rBase + e1 * amp
        const roMax = Math.max(ro0, ro1, rBase + em * amp)

        const [ix0, iy0] = polar(cx, cy, rInner, th0)
        const [ox0, oy0] = polar(cx, cy, ro0, th0)
        const [ox1, oy1] = polar(cx, cy, ro1, th1)
        const [ix1, iy1] = polar(cx, cy, rInner, th1)

        const cCore = lerpRgb(FILM_MINT, ringRgb, 0.25 + em * 0.35)
        const cMid = lerpRgb(ringRgb, FILM_AMBER, em * 0.75)
        const cHot = lerpRgb(cMid, FILM_AMBER, em * em * 0.85)

        const gr = g.createRadialGradient(cx, cy, rInner * 0.65, cx, cy, roMax + 5 * geomScale)
        gr.addColorStop(0, rgba(cCore, 0.05 + em * 0.1))
        gr.addColorStop(0.45, rgba(cMid, 0.14 + em * 0.38))
        gr.addColorStop(1, rgba(cHot, 0.22 + em * 0.52))

        g.beginPath()
        g.moveTo(ix0, iy0)
        g.lineTo(ox0, oy0)
        g.lineTo(ox1, oy1)
        g.lineTo(ix1, iy1)
        g.closePath()
        g.fillStyle = gr
        g.fill()
      }

      g.save()
      g.beginPath()
      for (let i = 0; i <= SEGMENTS; i += 1) {
        const idx = i % SEGMENTS
        const th = thOff + (i / SEGMENTS) * Math.PI * 2
        const ro = rBase + blurred[idx] * amp
        const [x, y] = polar(cx, cy, ro, th)
        if (i === 0) {
          g.moveTo(x, y)
        } else {
          g.lineTo(x, y)
        }
      }
      g.closePath()
      const rimA = lerpRgb(FILM_MINT, ringRgb, 0.35 + mean * 0.4)
      const rimB = lerpRgb(ringRgb, FILM_AMBER, 0.55 + mean * 0.35)
      const rim = g.createLinearGradient(
        cx + Math.cos(thOff) * rBase,
        cy + Math.sin(thOff) * rBase,
        cx - Math.cos(thOff) * rBase,
        cy - Math.sin(thOff) * rBase,
      )
      rim.addColorStop(0, rgba(rimA, 0.55))
      rim.addColorStop(0.5, rgba(rimB, 0.75))
      rim.addColorStop(1, rgba(FILM_AMBER, 0.5))
      const glowRgb = lerpRgb(rimA, rimB, 0.5)
      g.shadowBlur = (7 + mean * 20) * geomScale
      g.shadowColor = rgba(glowRgb, 0.35 + mean * 0.35)
      g.strokeStyle = rim
      g.lineWidth = 1.3 * geomScale
      g.lineJoin = 'round'
      g.stroke()
      g.restore()

      if (!audio.paused && analyser != null) {
        rafId = requestAnimationFrame(draw)
      }
    }

    const onPlay = () => {
      const kick = () => {
        void buildGraph().then((ok) => {
          stopRaf()
          if (ok && !audio.paused) {
            rafId = requestAnimationFrame(draw)
          }
        })
      }
      requestAnimationFrame(kick)
    }

    const onPause = () => {
      stopRaf()
      clearCanvas()
      void audioCtx?.suspend().catch(() => {})
    }

    audio.addEventListener('play', onPlay)
    audio.addEventListener('pause', onPause)
    audio.addEventListener('ended', onPause)

    if (!audio.paused) {
      void onPlay()
    }

    return () => {
      audio.removeEventListener('play', onPlay)
      audio.removeEventListener('pause', onPause)
      audio.removeEventListener('ended', onPause)
      stopRaf()
      clearCanvas()
      if (audioCtx != null && audioCtx.state !== 'closed') {
        void audioCtx.close().catch(() => {})
      }
      audioCtx = null
      analyser = null
      graphBuilt = false
    }
  }, [audio, audioUrl, ringColor, canvasCssPx, compact])

  if (audio == null || prefersReducedMotion()) {
    return null
  }

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none absolute inset-0 m-auto max-h-full max-w-full"
      aria-hidden
    />
  )
}
