import React from 'react'

function StatusPill({ status }) {
  const map = {
    normal: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
    low: 'bg-amber-50 text-amber-800 ring-amber-100',
    high: 'bg-rose-50 text-rose-700 ring-rose-100',
    unknown: 'bg-slate-50 text-slate-700 ring-slate-200',
  }
  const cls = map[status] || map.unknown
  return <div className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ${cls}`}>{String(status || 'unknown')}</div>
}

export default function HeartbeatResults({ result }) {
  if (!result) return null

  const bpm = typeof result.bpm === 'number' ? result.bpm : 0
  const plot = result.plot_png_base64
  const heartStatus = result.heart_status || 'unknown'

  return (
    <section className='mt-6 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200'>
      <div className='flex flex-wrap items-center justify-between gap-4'>
        <div>
          <div className='text-xs font-semibold tracking-widest text-sky-700'>RESULTS</div>
          <h3 className='mt-2 text-2xl font-semibold tracking-tight text-slate-900'>Your heartbeat summary</h3>
          <div className='mt-2 text-sm text-slate-600'>{result.message || 'Scan completed.'}</div>
        </div>

        <div className='flex items-center gap-3'>
          <StatusPill status={heartStatus} />
          <div className='rounded-2xl bg-slate-900 px-5 py-3 text-white'>
            <div className='text-xs text-white/70'>BPM</div>
            <div className='text-2xl font-semibold leading-none'>{bpm > 0 ? bpm.toFixed(1) : '—'}</div>
          </div>
        </div>
      </div>

      {plot ? (
        <img
          src={`data:image/png;base64,${plot}`}
          alt='Heartbeat plot'
          className='mt-5 w-full rounded-2xl bg-white p-3 shadow-sm ring-1 ring-slate-200'
        />
      ) : (
        <div className='mt-5 rounded-2xl bg-slate-50 p-5 text-sm text-slate-600 ring-1 ring-slate-200'>
          Plot not available (not enough stable signal). Try again with better lighting and keep your face still.
        </div>
      )}
    </section>
  )
}

