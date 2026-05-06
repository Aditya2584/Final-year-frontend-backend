import React, { useEffect, useMemo, useState } from 'react'
import { cancelAppointment, getAppointmentHistory, getUpcomingAppointments } from '../api/appointments'
import { useNavigate } from 'react-router-dom'

function StatusBadge({ status }) {
  const map = {
    Upcoming: 'bg-sky-50 text-sky-700 ring-sky-100',
    Completed: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
    Cancelled: 'bg-rose-50 text-rose-700 ring-rose-100',
  }
  const cls = map[status] || 'bg-slate-50 text-slate-700 ring-slate-200'
  return <span className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 ${cls}`}>{status}</span>
}

function AppointmentCard({ appt, onCancel }) {
  return (
    <div className='rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200'>
      <div className='flex flex-wrap items-start justify-between gap-4'>
        <div>
          <div className='text-sm font-semibold text-slate-900'>{appt.doctor || 'Any available doctor'}</div>
          <div className='mt-1 text-xs text-slate-500'>{appt.reason}</div>
          <div className='mt-3 text-sm text-slate-700'>
            <span className='font-semibold'>Date:</span> {appt.appointment_date} &nbsp;|&nbsp;{' '}
            <span className='font-semibold'>Time:</span> {appt.appointment_time}
          </div>
        </div>

        <div className='flex items-center gap-3'>
          <StatusBadge status={appt.status} />
          {appt.status === 'Upcoming' ? (
            <button
              onClick={() => onCancel(appt.id)}
              className='rounded-full bg-white px-4 py-2 text-sm font-semibold text-rose-700 ring-1 ring-rose-200 hover:bg-rose-50'
            >
              Cancel
            </button>
          ) : null}
        </div>
      </div>
    </div>
  )
}

export default function AppointmentDashboard() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [upcoming, setUpcoming] = useState([])
  const [history, setHistory] = useState([])
  const [query, setQuery] = useState('')

  const filteredUpcoming = useMemo(() => {
    if (!query.trim()) return upcoming
    const q = query.toLowerCase()
    return upcoming.filter((a) => (a.reason || '').toLowerCase().includes(q) || (a.doctor || '').toLowerCase().includes(q))
  }, [query, upcoming])

  const filteredHistory = useMemo(() => {
    if (!query.trim()) return history
    const q = query.toLowerCase()
    return history.filter((a) => (a.reason || '').toLowerCase().includes(q) || (a.doctor || '').toLowerCase().includes(q))
  }, [query, history])

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [u, h] = await Promise.all([getUpcomingAppointments(), getAppointmentHistory()])
      setUpcoming(u)
      setHistory(h)
    } catch (e) {
      setError(e?.message || 'Failed to load appointments.')
    } finally {
      setLoading(false)
    }
  }

  async function onCancel(id) {
    try {
      await cancelAppointment(id)
      await load()
    } catch (e) {
      setError(e?.message || 'Failed to cancel appointment.')
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div className='mx-auto max-w-screen-2xl px-4 pb-16'>
      <div className='rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200'>
        <div className='flex flex-wrap items-end justify-between gap-4'>
          <div>
            <div className='text-xs font-semibold tracking-widest text-sky-700'>DASHBOARD</div>
            <h1 className='mt-2 text-3xl font-semibold tracking-tight text-slate-900'>Appointments</h1>
            <p className='mt-2 text-sm text-slate-600'>View upcoming bookings and your appointment history.</p>
          </div>

          <div className='flex flex-wrap items-center gap-3'>
            <button
              onClick={() => navigate('/appointment')}
              className='rounded-full bg-sky-500 px-5 py-2.5 text-sm font-semibold text-white hover:bg-sky-600'
            >
              Book New
            </button>
            <button
              onClick={() => navigate('/')}
              className='rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800'
            >
              Home
            </button>
          </div>
        </div>

        <div className='mt-6 flex flex-wrap items-center justify-between gap-3'>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className='w-full max-w-md rounded-2xl bg-white px-4 py-3 text-sm ring-1 ring-slate-200 outline-none focus:ring-2 focus:ring-sky-400'
            placeholder='Search by doctor or reason…'
          />
          <button
            onClick={load}
            className='rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 ring-1 ring-slate-300 hover:bg-slate-50'
          >
            Refresh
          </button>
        </div>

        {loading ? <div className='mt-8 text-sm font-semibold text-slate-700'>Loading…</div> : null}
        {error ? (
          <div className='mt-8 rounded-2xl bg-rose-50 p-4 text-sm font-semibold text-rose-700 ring-1 ring-rose-100'>
            {error}
          </div>
        ) : null}

        <div className='mt-10 grid gap-10 lg:grid-cols-2'>
          <div>
            <div className='flex items-center justify-between'>
              <h2 className='text-lg font-semibold text-slate-900'>Upcoming</h2>
              <div className='text-xs text-slate-500'>{filteredUpcoming.length} item(s)</div>
            </div>
            <div className='mt-4 grid gap-4'>
              {filteredUpcoming.length ? (
                filteredUpcoming.map((a) => <AppointmentCard key={a.id} appt={a} onCancel={onCancel} />)
              ) : (
                <div className='rounded-2xl bg-slate-50 p-5 text-sm text-slate-600 ring-1 ring-slate-200'>
                  No upcoming appointments.
                </div>
              )}
            </div>
          </div>

          <div>
            <div className='flex items-center justify-between'>
              <h2 className='text-lg font-semibold text-slate-900'>History</h2>
              <div className='text-xs text-slate-500'>{filteredHistory.length} item(s)</div>
            </div>
            <div className='mt-4 grid gap-4'>
              {filteredHistory.length ? (
                filteredHistory.map((a) => <AppointmentCard key={a.id} appt={a} onCancel={onCancel} />)
              ) : (
                <div className='rounded-2xl bg-slate-50 p-5 text-sm text-slate-600 ring-1 ring-slate-200'>
                  No past appointments yet.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

