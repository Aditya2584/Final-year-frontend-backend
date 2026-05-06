import Navbar from './sections/Navbar'
import Hero from './sections/Hero'
import LogoStrip from './sections/LogoStrip'
import Steps from './sections/Steps'
import Doctors from './sections/Doctors'
import Footer from './sections/Footer'
import AppointmentBooking from './pages/AppointmentBooking'
import AppointmentDashboard from './pages/AppointmentDashboard'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useEffect } from 'react'

function App() {
  const location = useLocation()

  useEffect(() => {
    // Enable /#hash navigation to sections on the home page
    if (location.pathname !== '/') return

    if (!location.hash) {
      window.scrollTo({ top: 0, behavior: 'smooth' })
      return
    }

    const id = location.hash.replace('#', '')
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [location.pathname, location.hash])

  return (
    <div id='home' className='min-h-screen bg-slate-50 text-slate-900'>
      <div className='mx-auto max-w-screen-2xl px-4 py-6'>
        <Navbar />
      </div>

      <Routes>
        <Route
          path='/'
          element={
            <main className='mx-auto max-w-screen-2xl px-4 pb-16'>
              <Hero />
              <LogoStrip />
              <Steps />
              <Doctors />
            </main>
          }
        />
        <Route path='/appointment' element={<AppointmentBooking />} />
        <Route path='/appointments' element={<AppointmentDashboard />} />
        <Route path='*' element={<Navigate to='/' replace />} />
      </Routes>

      <Footer />
    </div>
  )
}

export default App
