import React from 'react'

const DOCTORS = [
  { name: 'Akshay Abhishek', role: 'Team Lead' },
  { name: 'Aditya Kumar Singh', role: 'Developer' },
  { name: 'Anish Singh', role: 'Documentation' },
  { name: 'Ashutosh Anand', role: 'Literature Reviewer' },
]

const Avatar = ({ seed }) => {
  const hue = (seed * 47) % 360
  return (
    <div
      className='h-24 w-24 rounded-2xl ring-1 ring-slate-200'
      style={{
        background: `linear-gradient(135deg, hsl(${hue} 90% 85%), hsl(${(hue + 40) % 360} 90% 92%))`,
      }}
    />
  )
}

const DoctorCard = ({ name, role, idx }) => {
  return (
    <div className='rounded-2xl bg-white p-5 text-center shadow-sm ring-1 ring-slate-200'>
      <div className='mx-auto grid place-items-center'>
        <Avatar seed={idx + 1} />
      </div>
      <div className='mt-4 text-sm font-semibold text-slate-900'>{name}</div>
      <div className='mt-1 text-xs text-slate-500'>{role}</div>
    </div>
  )
}

const Doctors = () => {
  return (
    <section id='doctor' className='mt-12'>
      <div className='rounded-3xl bg-slate-100/70 p-8 ring-1 ring-slate-200'>
        <div className='flex flex-wrap items-end justify-between gap-4'>
          <div>
            <div className='text-xs font-semibold tracking-widest text-sky-700'>MEET OUR DEVELOPERS</div>
            <h2 className='mt-2 text-2xl font-semibold tracking-tight sm:text-3xl'>
              We’re Dedicated To <br className='hidden sm:block' /> Your Well-Being
            </h2>
          </div>
          <div className='flex items-center gap-2'>
            <button className='grid h-10 w-10 place-items-center rounded-full bg-white ring-1 ring-slate-200 hover:bg-slate-50'>
              <span className='text-lg leading-none' aria-hidden='true'>
                ‹
              </span>
            </button>
            <button className='grid h-10 w-10 place-items-center rounded-full bg-sky-500 text-white shadow-sm hover:bg-sky-600'>
              <span className='text-lg leading-none' aria-hidden='true'>
                ›
              </span>
            </button>
          </div>
        </div>

        <div className='mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4'>
          {DOCTORS.map((d, idx) => (
            <DoctorCard key={`${d.role}-${idx}`} name={d.name} role={d.role} idx={idx} />
          ))}
        </div>
      </div>
    </section>
  )
}

export default Doctors

