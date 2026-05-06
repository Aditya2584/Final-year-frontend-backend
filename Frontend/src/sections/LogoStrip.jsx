import React from 'react'

const LogoPill = ({ name }) => {
  return (
    <div className='flex items-center gap-2 rounded-full bg-white/70 px-5 py-3 text-sm font-semibold text-slate-700 ring-1 ring-white/50'>
      <span className='inline-block h-2.5 w-2.5 rounded-full bg-slate-900/70' />
      {name}
    </div>
  )
}

const LogoStrip = () => {
  return (
    <section className='mt-10'>
      <div className='rounded-3xl bg-lime-200/70 px-6 py-6 ring-1 ring-lime-200'>
        <div className='flex flex-wrap items-center justify-center gap-4'>
          <LogoPill name='Good Lighting' />
          <LogoPill name='Click on "Check Your Beats"' />
          <LogoPill name='Lock Your Face' />
          <LogoPill name='Heat Beat & Data Plot' />
        </div>
      </div>
    </section>
  )
}

export default LogoStrip

