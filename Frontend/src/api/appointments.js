export async function createAppointment(payload) {
  const res = await fetch('/api/appointments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Request failed (${res.status})`)
  }

  return await res.json()
}

export async function getAppointments() {
  const res = await fetch('/api/appointments')
  if (!res.ok) throw new Error(`Request failed (${res.status})`)
  return await res.json()
}

export async function getUpcomingAppointments() {
  const res = await fetch('/api/appointments/upcoming')
  if (!res.ok) throw new Error(`Request failed (${res.status})`)
  return await res.json()
}

export async function getAppointmentHistory() {
  const res = await fetch('/api/appointments/history')
  if (!res.ok) throw new Error(`Request failed (${res.status})`)
  return await res.json()
}

export async function cancelAppointment(id) {
  const res = await fetch(`/api/appointments/${id}/cancel`, { method: 'PATCH' })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Request failed (${res.status})`)
  }
  return await res.json()
}

export async function rescheduleAppointment(id, payload) {
  const res = await fetch(`/api/appointments/${id}/reschedule`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `Request failed (${res.status})`)
  }
  return await res.json()
}

