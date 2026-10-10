import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Box, Button, Grid, MenuItem, TextField, Typography } from '@mui/material'
import BookingShell from './BookingShell'
import {
  loadBookingDraft,
  saveBookingDraft,
  holdBooking,
  confirmBooking,
} from '../../../features/public/publicBookingApi'

export default function BookingGuestPage() {
  const navigate = useNavigate()
  const draft = loadBookingDraft()
  const [form, setForm] = useState({
    guest_first_name: '',
    guest_last_name: '',
    guest_email: '',
    guest_phone: '',
    special_requests: '',
    payment_mode: 'deposit',
  })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (!draft?.room_type_id || !draft?.rate_plan_id) {
    return (
      <BookingShell>
        <Alert severity="warning" sx={{ mb: 2 }}>Select a rate first.</Alert>
        <Button variant="contained" onClick={() => navigate('/book')}>Back to search</Button>
      </BookingShell>
    )
  }

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const holdPayload = {
        property_id: draft.property_id,
        room_type_id: draft.room_type_id,
        rate_plan_id: draft.rate_plan_id,
        check_in: draft.check_in,
        check_out: draft.check_out,
        adults: draft.adults,
        children: draft.children,
        guest_email: form.guest_email,
        guest_name: `${form.guest_first_name} ${form.guest_last_name}`.trim(),
        guest_first_name: form.guest_first_name,
        guest_last_name: form.guest_last_name,
        guest_phone: form.guest_phone,
        special_requests: form.special_requests,
        payment_mode: form.payment_mode,
      }
      const hold = await holdBooking(holdPayload)
      const bookingId = hold.booking_id || hold.id
      const confirmed = await confirmBooking({
        booking_id: bookingId,
        guest_email: form.guest_email,
        payment_mode: form.payment_mode,
        payment_ref: form.payment_mode === 'pay_at_hotel' ? 'pay-at-hotel' : undefined,
      })
      const id = confirmed.booking_id || confirmed.id || bookingId
      saveBookingDraft({ ...draft, ...form, booking_id: id })
      navigate(`/book/confirmation/${id}`)
    } catch (err) {
      setError(err.data?.detail || err.data?.error || err.message || 'Booking failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <BookingShell subtitle={`${draft.room_type_name || 'Room'} · ${draft.rate_plan_name || 'Rate'} · €${Number(draft.total || 0).toFixed(2)}`}>
      <Typography variant="h6" sx={{ mb: 2, fontFamily: '"Fraunces", Georgia, serif' }}>
        Guest details
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Box component="form" onSubmit={handleSubmit}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth required label="First name" value={form.guest_first_name} onChange={set('guest_first_name')} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth required label="Last name" value={form.guest_last_name} onChange={set('guest_last_name')} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth required type="email" label="Email" value={form.guest_email} onChange={set('guest_email')} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label="Phone" value={form.guest_phone} onChange={set('guest_phone')} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              select
              fullWidth
              label="Payment"
              value={form.payment_mode}
              onChange={set('payment_mode')}
            >
              <MenuItem value="deposit">Deposit (30%)</MenuItem>
              <MenuItem value="full">Pay in full</MenuItem>
              <MenuItem value="pay_at_hotel">Pay at hotel</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12}>
            <TextField fullWidth multiline minRows={2} label="Special requests" value={form.special_requests} onChange={set('special_requests')} />
          </Grid>
          <Grid item xs={12} sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button onClick={() => navigate(-1)}>Back</Button>
            <Button type="submit" variant="contained" disabled={submitting} sx={{ minWidth: 160 }}>
              {submitting ? 'Confirming…' : 'Confirm booking'}
            </Button>
          </Grid>
        </Grid>
      </Box>
    </BookingShell>
  )
}
