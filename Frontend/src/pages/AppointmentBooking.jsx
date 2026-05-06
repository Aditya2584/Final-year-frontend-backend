import React, { useMemo, useState } from 'react'
import { createAppointment } from '../api/appointments'
import { useNavigate } from 'react-router-dom'

function todayISO() {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

const TIME_SLOTS = [
  '09:00',
  '09:30',
  '10:00',
  '10:30',
  '11:00',
  '11:30',
  '12:00',
  '14:00',
  '14:30',
  '15:00',
  '15:30',
  '16:00',
  '16:30',
  '17:00',
]

export default function AppointmentBooking() {
  const navigate = useNavigate()
  const minDate = useMemo(() => todayISO(), [])

  const [form, setForm] = useState({
    full_name: '',
    phone: '',
    email: '',
    reason: '',
    doctor: '',
    date: '',
    time: '',
  })
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  function update(key, value) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  function validate() {
    if (!form.full_name.trim()) return 'Full Name is required.'
    if (!form.phone.trim()) return 'Phone Number is required.'
    if (!form.reason.trim()) return 'Reason for Visit is required.'
    if (!form.date) return 'Appointment Date is required.'
    if (!form.time) return 'Appointment Time is required.'

    // Basic phone sanity
    const digits = form.phone.replace(/\D/g, '')
    if (digits.length < 10) return 'Phone Number looks invalid.'

    // Prevent past dates (extra safety; backend also validates)
    if (form.date < minDate) return 'Please select a future date.'
    return null
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    const msg = validate()
    if (msg) {
      setError(msg)
      return
    }

    setSubmitting(true)
    try {
      const payload = {
        full_name: form.full_name.trim(),
        phone: form.phone.trim(),
        email: form.email.trim() || null,
        reason: form.reason.trim(),
        doctor: form.doctor.trim() || null,
        appointment_date: form.date,
        appointment_time: form.time,
      }
      const created = await createAppointment(payload)
      setSuccess('Appointment booked successfully.')
      setTimeout(() => navigate('/appointments', { state: { createdId: created.id } }), 600)
    } catch (e2) {
      setError(e2?.message || 'Failed to submit appointment.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className='mx-auto max-w-screen-2xl px-4 pb-16'>
      <div className='rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200'>
        <div className='flex flex-wrap items-end justify-between gap-4'>
          <div>
            <div className='text-xs font-semibold tracking-widest text-sky-700'>APPOINTMENT</div>
            <h1 className='mt-2 text-3xl font-semibold tracking-tight text-slate-900'>Book an appointment</h1>
            <p className='mt-2 text-sm text-slate-600'>Fill in the details below. We’ll confirm your booking shortly.</p>
          </div>
          <button
            type='button'
            onClick={() => navigate('/')}
            className='rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800'
          >
            Back to Home
          </button>
        </div>

        <form onSubmit={onSubmit} className='mt-8 grid gap-5 lg:grid-cols-2'>
          <label className='grid gap-2'>
            <span className='text-sm font-semibold text-slate-900'>Full Name *</span>
            <input
              value={form.full_name}
              onChange={(e) => update('full_name', e.target.value)}
              className='rounded-2xl bg-white px-4 py-3 text-sm ring-1 ring-slate-200 outline-none focus:ring-2 focus:ring-sky-400'
              placeholder='Your full name'
              autoComplete='name'
            />
          </label>

          <label className='grid gap-2'>
            <span className='text-sm font-semibold text-slate-900'>Phone Number *</span>
            <input
              value={form.phone}
              onChange={(e) => update('phone', e.target.value)}
              className='rounded-2xl bg-white px-4 py-3 text-sm ring-1 ring-slate-200 outline-none focus:ring-2 focus:ring-sky-400'
              placeholder='10-digit phone'
              autoComplete='tel'
            />
          </label>

          <label className='grid gap-2'>
            <span className='text-sm font-semibold text-slate-900'>Email (optional)</span>
            <input
              value={form.email}
              onChange={(e) => update('email', e.target.value)}
              type='email'
              className='rounded-2xl bg-white px-4 py-3 text-sm ring-1 ring-slate-200 outline-none focus:ring-2 focus:ring-sky-400'
              placeholder='you@example.com'
              autoComplete='email'
            />
          </label>

          <label className='grid gap-2'>
            <span className='text-sm font-semibold text-slate-900'>Specific Doctor (optional)</span>
            <input
              value={form.doctor}
              onChange={(e) => update('doctor', e.target.value)}
              className='rounded-2xl bg-white px-4 py-3 text-sm ring-1 ring-slate-200 outline-none focus:ring-2 focus:ring-sky-400'
              placeholder='e.g. Dr. Sharma'
            />
          </label>

          <label className='grid gap-2 lg:col-span-2'>
            <span className='text-sm font-semibold text-slate-900'>Reason for Visit *</span>
            <textarea
              value={form.reason}
              onChange={(e) => update('reason', e.target.value)}
              className='min-h-28 rounded-2xl bg-white px-4 py-3 text-sm ring-1 ring-slate-200 outline-none focus:ring-2 focus:ring-sky-400'
              placeholder='Describe your symptoms or reason'
            />
          </label>

          <label className='grid gap-2'>
            <span className='text-sm font-semibold text-slate-900'>Appointment Date *</span>
            <input
              value={form.date}
              onChange={(e) => update('date', e.target.value)}
              type='date'
              min={minDate}
              className='rounded-2xl bg-white px-4 py-3 text-sm ring-1 ring-slate-200 outline-none focus:ring-2 focus:ring-sky-400'
            />
          </label>

          <label className='grid gap-2'>
            <span className='text-sm font-semibold text-slate-900'>Appointment Time *</span>
            <select
              value={form.time}
              onChange={(e) => update('time', e.target.value)}
              className='rounded-2xl bg-white px-4 py-3 text-sm ring-1 ring-slate-200 outline-none focus:ring-2 focus:ring-sky-400'
            >
              <option value=''>Select a time slot</option>
              {TIME_SLOTS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>

          {error ? (
            <div className='lg:col-span-2 rounded-2xl bg-rose-50 p-4 text-sm font-semibold text-rose-700 ring-1 ring-rose-100'>
              {error}
            </div>
          ) : null}

          {success ? (
            <div className='lg:col-span-2 rounded-2xl bg-emerald-50 p-4 text-sm font-semibold text-emerald-700 ring-1 ring-emerald-100'>
              {success}
            </div>
          ) : null}

          <div className='lg:col-span-2 flex items-center justify-end gap-3'>
            <button
              type='submit'
              disabled={submitting}
              className='rounded-full bg-sky-500 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-sky-600 disabled:cursor-not-allowed disabled:opacity-60'
            >
              {submitting ? 'Submitting…' : 'Submit Appointment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

