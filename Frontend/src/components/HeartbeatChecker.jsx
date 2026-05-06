import React, { useEffect, useMemo, useRef, useState } from 'react'

const POLL_MS = 1000

function PlotImage({ plotBase64 }) {
  if (!plotBase64) return null
  return (
    <img
      src={`data:image/png;base64,${plotBase64}`}
      alt='Heartbeat plot'
      className='mt-4 w-full rounded-2xl bg-white p-3 shadow-sm ring-1 ring-slate-200'
    />
  )
}

export default function HeartbeatChecker() {
  const [status, setStatus] = useState('idle') // idle | running | done | error
  const [jobId, setJobId] = useState(null)
  const [bpm, setBpm] = useState(null)
  const [message, setMessage] = useState(null)
  const [plotBase64, setPlotBase64] = useState(null)
  const [error, setError] = useState(null)

  const pollTimer = useRef(null)

  const canStart = status === 'idle' || status === 'done' || status === 'error'

  const pill = useMemo(() => {
    if (status === 'running') return { text: 'Measuring… keep your face in frame', cls: 'bg-sky-50 text-sky-700 ring-sky-100' }
    if (status === 'done') return { text: 'Done', cls: 'bg-emerald-50 text-emerald-700 ring-emerald-100' }
    if (status === 'error') return { text: 'Error', cls: 'bg-rose-50 text-rose-700 ring-rose-100' }
    return { text: 'Ready', cls: 'bg-slate-50 text-slate-700 ring-slate-200' }
  }, [status])

  async function start() {
    if (!canStart) return
    setStatus('running')
    setError(null)
    setBpm(null)
    setMessage(null)
    setPlotBase64(null)

    try {
      const res = await fetch('/api/heartbeat/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration_sec: 15, camera_index: 0 }),
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(text || `Request failed (${res.status})`)
      }

      const data = await res.json()
      setJobId(data.job_id)
    } catch (e) {
      setStatus('error')
      setError(e?.message || 'Failed to start heartbeat capture.')
    }
  }

  async function poll(id) {
    try {
      const res = await fetch(`/api/heartbeat/${id}`)
      if (!res.ok) throw new Error(`Polling failed (${res.status})`)
      const data = await res.json()

      if (data.status === 'running') return
      if (data.status === 'error') {
        setStatus('error')
        setError(data.error || 'Backend error while capturing heartbeat.')
        return
      }

      setStatus('done')
      setBpm(typeof data.bpm === 'number' ? data.bpm : null)
      setMessage(data.message || null)
      setPlotBase64(data.plot_png_base64 || null)
    } catch (e) {
      setStatus('error')
      setError(e?.message || 'Error while polling heartbeat result.')
    }
  }

  useEffect(() => {
    if (!jobId || status !== 'running') return

    pollTimer.current = window.setInterval(() => poll(jobId), POLL_MS)
    poll(jobId)

    return () => {
      if (pollTimer.current) window.clearInterval(pollTimer.current)
      pollTimer.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, status])

  return (
    <div className='mt-6 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200'>
      <div className='flex flex-wrap items-center justify-between gap-3'>
        <div>
          <div className='text-sm font-semibold text-slate-900'>Heartbeat</div>
          <div className='mt-1 text-xs text-slate-600'>Camera starts only after you click the button.</div>
        </div>
        <div className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ${pill.cls}`}>{pill.text}</div>
      </div>

      <div className='mt-4 flex flex-wrap items-center gap-3'>
        <button
          onClick={start}
          disabled={!canStart}
          className='rounded-full bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60'
        >
          {status === 'running' ? 'Measuring…' : 'Check Your Beats'}
        </button>

        {bpm ? (
          <div className='text-sm font-semibold text-slate-900'>
            Current BPM: <span className='text-sky-600'>{bpm.toFixed(1)}</span>
          </div>
        ) : null}
      </div>

      {message ? <div className='mt-3 text-sm text-slate-700'>{message}</div> : null}
      {error ? <div className='mt-3 text-sm font-semibold text-rose-700'>{error}</div> : null}

      <PlotImage plotBase64={plotBase64} />
    </div>
  )
}

