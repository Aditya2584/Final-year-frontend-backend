import React, { useState } from 'react'
import HeartbeatScanModal from '../components/HeartbeatScanModal'
import HeartbeatResults from '../components/HeartbeatResults'
import { useNavigate } from 'react-router-dom'

const StatCard = ({ title, value, sub }) => {
  return (
    <div className='rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200'>
      <div className='text-sm font-medium text-slate-500'>{title}</div>
      <div className='mt-2 text-3xl font-semibold tracking-tight'>{value}</div>
      {sub ? <div className='mt-1 text-sm text-slate-500'>{sub}</div> : null}
    </div>
  )
}

const Hero = () => {
  const [scanOpen, setScanOpen] = useState(false)
  const [scanResult, setScanResult] = useState(null)
  const navigate = useNavigate()

  return (
    <section className='rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200'>
      <div className='grid items-center gap-8 lg:grid-cols-2'>
        <div>
          <div className='inline-flex items-center gap-2 rounded-full bg-sky-50 px-3 py-1 text-sm font-medium text-sky-700 ring-1 ring-sky-100'>
            <span className='h-2 w-2 rounded-full bg-sky-500' />
            Trusted <span >&#9679;</span> Contactless <span >&#9679;</span> Simplified
          </div>

          <h1 className='mt-4 text-4xl font-semibold leading-tight tracking-tight sm:text-5xl'>
            Monitoring Every Beat <br></br> <span className='text-sky-600'>Touch-Free</span>
          </h1>

          <p className='mt-4 max-w-xl text-base leading-relaxed text-slate-600'>
          Monitor heartbeats without physical contact. Experience smarter, safer, and seamless health tracking powered by innovative technology.
          </p>

          <div className='mt-6 flex flex-wrap items-center gap-3'>
            <button
              onClick={() => setScanOpen(true)}
              className='rounded-full bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-slate-800'
            >
              Check Your Beats
            </button>
            <button
              onClick={() => navigate('/appointment')}
              className='rounded-full bg-white px-5 py-2.5 text-sm font-semibold text-slate-900 ring-1 ring-slate-300 hover:bg-slate-50'
            >
              Book an Appointment
            </button>
          </div>

          <HeartbeatResults result={scanResult} />
        </div>

        <div className='relative'>
          <div className='aspect-4/3 w-full overflow-hidden rounded-3xl bg-linear-to-br from-sky-50 to-slate-50 ring-1 ring-slate-200'>
            <img
              src='/assets/doct-pat.png'
              alt='Doctor and patient'
              className='h-full w-full object-contain p-6 opacity-95 mix-blend-multiply'
              loading='lazy'
            />
            <div className='pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-linear-to-t from-slate-50 to-transparent' />
          </div>

          <div className='mt-6 grid gap-4 sm:grid-cols-2'>
            <StatCard title='Accuracy rate' value='88%' sub='Healing progress' />
            <StatCard title='Support' value='24/7' sub='Fast response time' />
          </div>
        </div>
      </div>

      <HeartbeatScanModal
        open={scanOpen}
        onClose={() => setScanOpen(false)}
        onComplete={(res) => setScanResult(res)}
        durationSec={12}
      />
    </section>
  )
}

export default Hero

