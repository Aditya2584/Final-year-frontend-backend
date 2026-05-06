import React from 'react'
import { Link } from 'react-router-dom'

const Navbar = () => {
  return (
    <header className='rounded-3xl bg-white px-5 py-3 shadow-sm ring-1 ring-slate-200'>
      <div className='flex items-center justify-between gap-4'>
        <div className='flex items-center gap-2'>
          <div className='grid h-9 w-9 place-items-center rounded-xl bg-slate-900 text-white'>
            <span className='text-sm font-bold'>V</span>
          </div>
          <div className='text-sm font-extrabold tracking-wide text-slate-900'>VitalLink</div>
        </div>

        <nav className='hidden items-center gap-7 text-sm font-semibold text-slate-700 md:flex'>
          <Link className='hover:text-slate-900' to='/'>
            Home
          </Link>
          <Link className='hover:text-slate-900' to='/#doctor'>
            Doctor
          </Link>
          <Link className='hover:text-slate-900' to='/appointments'>
            Appointments
          </Link>
          <Link className='hover:text-slate-900' to='/#steps'>
            Steps
          </Link>
        </nav>

        <div className='flex items-center gap-3'>
          <button className='rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-900 ring-1 ring-slate-300 hover:bg-slate-50'>
            Log in
          </button>
          <button className='rounded-full bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-slate-800'>
            Create an account
          </button>
        </div>
      </div>
    </header>
  )
}

export default Navbar
