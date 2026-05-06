import React, { useEffect, useMemo, useRef, useState } from 'react'

function clamp01(x) {
  return Math.max(0, Math.min(1, x))
}

function HeartPulse() {
  return (
    <div className='relative h-10 w-10'>
      <div className='absolute inset-0 rounded-full bg-sky-400/30 animate-ping' />
      <div className='absolute inset-1 rounded-full bg-sky-500/30' />
      <div className='absolute inset-3 rounded-full bg-sky-600' />
    </div>
  )
}

function ModalShell({ open, onClose, children }) {
  if (!open) return null
  return (
    <div className='fixed inset-0 z-50'>
      <div className='absolute inset-0 bg-slate-900/50 backdrop-blur-sm' onClick={onClose} />
      <div className='absolute inset-0 grid place-items-center p-4'>
        <div className='w-full max-w-4xl overflow-hidden rounded-3xl bg-white shadow-2xl ring-1 ring-slate-200'>
          {children}
        </div>
      </div>
    </div>
  )
}

export default function HeartbeatScanModal({ open, onClose, onComplete, durationSec = 12 }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const sendTimerRef = useRef(null)
  const startedAtRef = useRef(0)
  const sessionIdRef = useRef(null)

  const [uiState, setUiState] = useState('idle') // idle | requesting_camera | scanning | finishing | error
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(0)
  const [liveBpm, setLiveBpm] = useState(null)
  const [heartStatus, setHeartStatus] = useState('unknown')

  const title = useMemo(() => {
    if (uiState === 'requesting_camera') return 'Starting camera…'
    if (uiState === 'scanning') return 'Scanning your heartbeat…'
    if (uiState === 'finishing') return 'Finalizing results…'
    return 'Check Your Beats'
  }, [uiState])

  function stopCamera() {
    if (sendTimerRef.current) {
      window.clearInterval(sendTimerRef.current)
      sendTimerRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
  }

  async function start() {
    setError(null)
    setLiveBpm(null)
    setHeartStatus('unknown')
    setProgress(0)
    setUiState('requesting_camera')

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
    } catch (e) {
      setUiState('error')
      setError('Camera permission denied or camera not available.')
      return
    }

    // Start backend session only after popup + camera preview are ready.
    try {
      const res = await fetch('/api/heartbeat/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration_sec: durationSec }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      sessionIdRef.current = data.session_id
    } catch (e) {
      stopCamera()
      setUiState('error')
      setError(e?.message || 'Failed to start backend scan session.')
      return
    }

    startedAtRef.current = Date.now()
    setUiState('scanning')

    // Send frames periodically.
    sendTimerRef.current = window.setInterval(async () => {
      const sid = sessionIdRef.current
      const video = videoRef.current
      const canvas = canvasRef.current
      if (!sid || !video || !canvas) return

      const elapsed = (Date.now() - startedAtRef.current) / 1000
      setProgress(clamp01(elapsed / durationSec))

      const w = 320
      const h = 240
      canvas.width = w
      canvas.height = h
      const ctx = canvas.getContext('2d', { willReadFrequently: false })
      ctx.drawImage(video, 0, 0, w, h)

      const blob = await new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.7))
      if (!blob) return

      try {
        const fd = new FormData()
        fd.append('frame', blob, 'frame.jpg')
        const r = await fetch(`/api/heartbeat/session/${sid}/frame`, { method: 'POST', body: fd })
        if (!r.ok) throw new Error(await r.text())
        const out = await r.json()
        if (typeof out.bpm === 'number' && out.bpm > 0) setLiveBpm(out.bpm)
        if (out.heart_status) setHeartStatus(out.heart_status)
        if (typeof out.progress === 'number') setProgress(clamp01(out.progress))

        if (out.status === 'done') {
          await finish()
        }
      } catch (e) {
        setUiState('error')
        setError(e?.message || 'Error while scanning.')
        stopCamera()
      }
    }, 350)
  }

  async function finish() {
    if (uiState === 'finishing') return
    setUiState('finishing')

    const sid = sessionIdRef.current
    stopCamera()

    if (!sid) {
      setUiState('error')
      setError('Scan session missing.')
      return
    }

    try {
      const r = await fetch(`/api/heartbeat/session/${sid}/finish`, { method: 'POST' })
      if (!r.ok) throw new Error(await r.text())
      const data = await r.json()
      onComplete?.(data)
      onClose?.()
      setUiState('idle')
    } catch (e) {
      setUiState('error')
      setError(e?.message || 'Failed to finalize scan.')
    }
  }

  useEffect(() => {
    if (!open) {
      stopCamera()
      sessionIdRef.current = null
      setUiState('idle')
      setError(null)
      setProgress(0)
      setLiveBpm(null)
      setHeartStatus('unknown')
      return
    }
    start()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  useEffect(() => {
    return () => stopCamera()
  }, [])

  return (
    <ModalShell open={open} onClose={onClose}>
      <div className='flex flex-col gap-0 lg:flex-row'>
        <div className='relative flex-1 bg-slate-900'>
          <video ref={videoRef} className='h-full w-full object-cover' playsInline muted />
          <div className='pointer-events-none absolute inset-0 bg-linear-to-t from-slate-900/40 to-transparent' />
          <div className='pointer-events-none absolute left-5 top-5 flex items-center gap-3 rounded-2xl bg-white/10 px-4 py-3 text-white backdrop-blur'>
            <HeartPulse />
            <div>
              <div className='text-sm font-semibold'>{title}</div>
              <div className='mt-0.5 text-xs text-white/80'>Please stay still while we analyze your pulse.</div>
            </div>
          </div>
        </div>

        <div className='w-full max-w-xl p-6'>
          <div className='flex items-start justify-between gap-4'>
            <div>
              <div className='text-xs font-semibold tracking-widest text-sky-700'>LIVE SCAN</div>
              <h3 className='mt-2 text-2xl font-semibold tracking-tight text-slate-900'>Heartbeat scan</h3>
              <p className='mt-2 text-sm text-slate-600'>Keep your face well-lit and centered in the frame.</p>
            </div>
            <button
              onClick={() => {
                stopCamera()
                onClose?.()
              }}
              className='rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800'
            >
              Close
            </button>
          </div>

          <div className='mt-6 rounded-2xl bg-slate-50 p-5 ring-1 ring-slate-200'>
            <div className='flex items-center justify-between gap-4'>
              <div className='text-sm font-semibold text-slate-900'>Progress</div>
              <div className='text-sm font-semibold text-sky-700'>{Math.round(progress * 100)}%</div>
            </div>
            <div className='mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-200'>
              <div className='h-full rounded-full bg-sky-500 transition-[width] duration-300' style={{ width: `${Math.round(progress * 100)}%` }} />
            </div>
            <div className='mt-4 flex flex-wrap items-center justify-between gap-3'>
              <div className='text-sm text-slate-700'>
                {uiState === 'error' ? (
                  <span className='font-semibold text-rose-700'>{error}</span>
                ) : (
                  <span>
                    <span className='font-semibold'>Scanning your heartbeat…</span> stay still for best results.
                  </span>
                )}
              </div>

              <div className='rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 ring-1 ring-slate-200'>
                {liveBpm ? `${liveBpm.toFixed(1)} BPM` : '— BPM'}
              </div>
            </div>

            <div className='mt-3 text-xs text-slate-500'>
              Status: <span className='font-semibold capitalize text-slate-700'>{heartStatus}</span>
            </div>
          </div>

          <div className='mt-4 text-xs text-slate-500'>
            If you see an error, check camera permissions in your browser and try again.
          </div>
        </div>
      </div>

      <canvas ref={canvasRef} className='hidden' />
    </ModalShell>
  )
}

