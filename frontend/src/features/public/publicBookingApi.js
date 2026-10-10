/**
 * Public booking-engine helpers (no JWT).
 * Uses fetch against VITE_API_BASE_URL so anonymous guests are not redirected to /login.
 *
 * Hold responses include `{ booking_id, hold_token, ... }`. Confirm / cancel / modify /
 * confirmation lookups must send the same `hold_token` (body or ?hold_token=).
 */

const baseUrl = () => (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '')

async function publicRequest(path, { method = 'GET', body } = {}) {
  const res = await fetch(`${baseUrl()}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: body != null ? JSON.stringify(body) : undefined,
  })
  const text = await res.text()
  let data = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = { detail: text }
  }
  if (!res.ok) {
    const err = new Error(data?.detail || data?.error || `Request failed (${res.status})`)
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}

export function quoteAvailability(payload) {
  return publicRequest('/availability/quote/', { method: 'POST', body: payload })
}

export function holdBooking(payload) {
  return publicRequest('/booking-engine/hold/', { method: 'POST', body: payload })
}

export function confirmBooking(payload) {
  return publicRequest('/booking-engine/confirm/', { method: 'POST', body: payload })
}

export function getConfirmation(id, holdToken) {
  const q = holdToken ? `?hold_token=${encodeURIComponent(holdToken)}` : ''
  return publicRequest(`/booking-engine/confirmation/${id}/${q}`, { method: 'GET' })
}

export function cancelHold(bookingId, holdToken) {
  return publicRequest('/booking-engine/cancel/', {
    method: 'POST',
    body: {
      booking_id: Number(bookingId),
      hold_token: holdToken || '',
    },
  })
}

export function modifyHold(bookingId, payload) {
  return publicRequest(`/booking-engine/holds/${bookingId}/modify/`, {
    method: 'POST',
    body: payload,
  })
}

const BOOKING_DRAFT_KEY = 'nephele_booking_draft'

export function saveBookingDraft(draft) {
  sessionStorage.setItem(BOOKING_DRAFT_KEY, JSON.stringify(draft))
}

export function loadBookingDraft() {
  try {
    const raw = sessionStorage.getItem(BOOKING_DRAFT_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function clearBookingDraft() {
  sessionStorage.removeItem(BOOKING_DRAFT_KEY)
}
