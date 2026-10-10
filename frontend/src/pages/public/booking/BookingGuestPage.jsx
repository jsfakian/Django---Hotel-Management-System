import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Box, Button, Grid, MenuItem, TextField, Typography } from '@mui/material'
import BookingShell from './BookingShell'
import { useBookingT } from './bookingLang'
import {
  loadBookingDraft,
  saveBookingDraft,
  holdBooking,
  confirmBooking,
} from '../../../features/public/publicBookingApi'

function GuestForm({ draft }) {
  const navigate = useNavigate()
  const { t } = useBookingT()
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
      const paymentRef = form.payment_mode === 'pay_at_hotel' ? 'pay-at-hotel' : undefined
      const confirmed = await confirmBooking({
        booking_id: bookingId,
        guest_email: form.guest_email,
        payment_mode: form.payment_mode,
        payment_ref: paymentRef,
      })
      const id = confirmed.booking_id || confirmed.id || bookingId
      saveBookingDraft({ ...draft, ...form, booking_id: id })

      if (confirmed.checkout_url) {
        window.location.href = confirmed.checkout_url
        return
      }
      if (confirmed.client_secret) {
        navigate(`/book/confirmation/${id}`, {
          state: { client_secret: confirmed.client_secret },
        })
        return
      }
      navigate(`/book/confirmation/${id}`)
    } catch (err) {
      setError(err.data?.detail || err.data?.error || err.message || t('bookingFailed'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <Typography variant="h6" sx={{ mb: 2, fontFamily: '"Fraunces", Georgia, serif' }}>
        {t('guestDetails')}
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Box component="form" onSubmit={handleSubmit}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth required label={t('firstName')} value={form.guest_first_name} onChange={set('guest_first_name')} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth required label={t('lastName')} value={form.guest_last_name} onChange={set('guest_last_name')} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth required type="email" label={t('email')} value={form.guest_email} onChange={set('guest_email')} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label={t('phone')} value={form.guest_phone} onChange={set('guest_phone')} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField select fullWidth label={t('payment')} value={form.payment_mode} onChange={set('payment_mode')}>
              <MenuItem value="deposit">{t('deposit')}</MenuItem>
              <MenuItem value="full">{t('payFull')}</MenuItem>
              <MenuItem value="pay_at_hotel">{t('payAtHotel')}</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12}>
            <TextField fullWidth multiline minRows={2} label={t('specialRequests')} value={form.special_requests} onChange={set('special_requests')} />
          </Grid>
          <Grid item xs={12} sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button onClick={() => navigate(-1)}>{t('back')}</Button>
            <Button type="submit" variant="contained" disabled={submitting} sx={{ minWidth: 160 }}>
              {submitting ? t('confirming') : t('confirmBooking')}
            </Button>
          </Grid>
        </Grid>
      </Box>
    </>
  )
}

function MissingDraftBody() {
  const navigate = useNavigate()
  const { t } = useBookingT()
  return (
    <>
      <Alert severity="warning" sx={{ mb: 2 }}>{t('selectRateFirst')}</Alert>
      <Button variant="contained" onClick={() => navigate('/book')}>{t('backToSearch')}</Button>
    </>
  )
}

function MissingDraft() {
  return (
    <BookingShell>
      <MissingDraftBody />
    </BookingShell>
  )
}

export default function BookingGuestPage() {
  const draft = loadBookingDraft()
  if (!draft?.room_type_id || !draft?.rate_plan_id) {
    return <MissingDraft />
  }
  return (
    <BookingShell subtitle={`${draft.room_type_name || 'Room'} · ${draft.rate_plan_name || 'Rate'} · €${Number(draft.total || 0).toFixed(2)}`}>
      <GuestForm draft={draft} />
    </BookingShell>
  )
}
