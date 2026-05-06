import React from 'react'

const Footer = () => {
  return (
    <footer className='mt-16 border-t border-slate-200 bg-white'>
      <div className='mx-auto max-w-screen-2xl px-4 py-10'>
        <div className='flex flex-col justify-between gap-6 sm:flex-row sm:items-center'>
          <div>
            <div className='text-sm font-extrabold tracking-wide text-slate-900'>VitalLink</div>
            <div className='mt-1 text-sm text-slate-600'>A modern contactless healthcare</div>
          </div>
          <div className='flex flex-wrap items-center gap-4 text-sm font-semibold text-slate-700'>
            <a className='hover:text-slate-900' href='#about'>
              About
            </a>
            <a className='hover:text-slate-900' href='#doctor'>
              Doctor
            </a>
            <a className='hover:text-slate-900' href='#blog'>
              Blog
            </a>
            <a className='hover:text-slate-900' href='#contact'>
              Contact
            </a>
          </div>
        </div>
        <div className='mt-8 text-xs text-slate-500'>© {new Date().getFullYear()} VitalLink. All rights reserved.</div>
      </div>
    </footer>
  )
}

export default Footer

