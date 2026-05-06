import React from 'react'

const StepCard = ({ title, desc, icon, highlighted }) => {
  return (
    <div
      className={[
        'rounded-2xl p-6 ring-1 transition',
        highlighted
          ? 'bg-sky-500 text-white ring-sky-400 shadow-sm'
          : 'bg-white text-slate-900 ring-slate-200 hover:shadow-sm',
      ].join(' ')}
    >
      <div
        className={[
          'grid h-12 w-12 place-items-center rounded-xl',
          highlighted ? 'bg-white/15' : 'bg-slate-900/5',
        ].join(' ')}
      >
        {icon}
      </div>
      <h3 className='mt-4 text-base font-semibold'>{title}</h3>
      <p className={['mt-2 text-sm leading-relaxed', highlighted ? 'text-white/85' : 'text-slate-600'].join(' ')}>
        {desc}
      </p>
    </div>
  )
}

const Icon = ({ path, className }) => (
  <svg viewBox='0 0 24 24' className={className} fill='none' xmlns='http://www.w3.org/2000/svg' aria-hidden='true'>
    <path d={path} stroke='currentColor' strokeWidth='2' strokeLinecap='round' strokeLinejoin='round' />
  </svg>
)

const Steps = () => {
  return (
    <section id='steps' className='mt-12 rounded-3xl bg-white p-8 shadow-sm ring-1 ring-slate-200'>
      <div className='text-center'>
        <h2 className='text-2xl font-semibold tracking-tight sm:text-3xl'>4 Easy Steps And Get Your Solution</h2>
        <p className='mx-auto mt-3 max-w-2xl text-sm leading-relaxed text-slate-600'>
          Keep things simple: find the right doctor, request a consultation, schedule a meeting, and get your solution.
        </p>
      </div>

      <div className='mt-8 grid gap-5 md:grid-cols-2 lg:grid-cols-4'>
        <StepCard
          title='Create Your Account'
          desc='Sign up securely to access personalized health monitoring, heartbeat history, and medical support anytime.'
          icon={<Icon className='h-6 w-6' path='M4 20v-2a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4v2M12 10a4 4 0 1 0 0-8 4 4 0 0 0 0 8' />}
        />
        <StepCard
          title='Check Your Heartbeat'
          desc='Click on “Check Your Beats” to instantly monitor your heartbeat using advanced contactless technology.'
          highlighted
          icon={<Icon className='h-6 w-6' path='M21 15a4 4 0 0 1-4 4H7l-4 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8Z' />}
        />
        <StepCard
          title='View Health Statistics'
          desc='Analyze your heartbeat data with real-time stats, trends, and visual graphs for better health insights.'
          icon={<Icon className='h-6 w-6' path='M8 7V3m8 4V3M4 11h16M6 5h12a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z' />}
        />
        <StepCard
          title='Consult a Doctor'
          desc='Connect with healthcare professionals, get expert advice, or book an appointment for further diagnosis and care.'
          icon={<Icon className='h-6 w-6' path='M20 7 9 18l-5-5' />}
        />
      </div>
    </section>
  )
}

export default Steps

