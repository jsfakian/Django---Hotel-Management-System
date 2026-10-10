import React, { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Alert, Box, Button, Grid, MenuItem, TextField, Typography } from '@mui/material'
import BookingShell from './BookingShell'
import { useBookingT } from './bookingLang'
import {
  loadBookingDraft,
  saveBookingDraft,
  holdBooking,
  confirmBooking,
} from '../../../features/public/publicBookingApi'

function paymentReturnState(location) {
  const params = new URLSearchParams(location.search || '')
  const paymentRef = params.get('payment_ref')
    || params.get('ref')
    || location.state?.payment_ref
  const verified = params.get('paid') === '1'
    || params.get('status') === 'paid'
    || Boolean(location.state?.payment_verified)
  return { paymentRef, verified }
}

function confirmationPath(bookingId, holdToken) {
  if (!holdToken) return `/book/confirmation/${bookingId}`
  return `/book/confirmation/${bookingId}?token=${encodeURIComponent(holdToken)}`
}

function persistGuestDraft(draft, form, bookingId, holdToken) {
  saveBookingDraft({
    ...draft,
    ...form,
    booking_id: bookingId,
    hold_token: holdToken,
  })
}

async function confirmPayAtHotel({ bookingId, holdToken, form }) {
  return confirmBooking({
    booking_id: bookingId,
    hold_token: holdToken,
    guest_email: form.guest_email,
    payment_mode: form.payment_mode,
    payment_ref: 'pay-at-hotel',
  })
}

function navigateAfterHold(navigate, { hold, bookingId, holdToken, paymentMode }) {
  if (hold.checkout_url) {
    window.location.href = hold.checkout_url
    return 'redirect'
  }
  if (paymentMode === 'pay_at_hotel') return 'confirm_hotel'
  if (hold.client_secret) {
    navigate(confirmationPath(bookingId, holdToken), {
      state: { client_secret: hold.client_secret, hold_token: holdToken },
    })
    return 'done'
  }
  navigate(confirmationPath(bookingId, holdToken), { state: { hold_token: holdToken } })
  return 'done'
}

function usePaymentReturnConfirm({ draft, form, setError, setSubmitting, t }) {
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    const { paymentRef, verified } = paymentReturnState(location)
    const bookingId = draft.booking_id
    const holdToken = draft.hold_token
    if (!verified || !paymentRef || !bookingId || !holdToken) return undefined

    let cancelled = false
    ;(async () => {
      setSubmitting(true)
      setError('')
      try {
        const confirmed = await confirmBooking({
          booking_id: bookingId,
          hold_token: holdToken,
          guest_email: draft.guest_email || form.guest_email,
          payment_mode: draft.payment_mode || form.payment_mode,
          payment_ref: paymentRef,
        })
        if (cancelled) return
        const id = confirmed.booking_id || confirmed.id || bookingId
        persistGuestDraft(draft, form, id, holdToken)
        navigate(confirmationPath(id, holdToken), { replace: true })
      } catch (err) {
        if (!cancelled) {
          setError(err.data?.detail || err.data?.error || err.message || t('bookingFailed'))
        }
      } finally {
        if (!cancelled) setSubmitting(false)
      }
    })()
    return () => { cancelled = true }
    // Run once on mount for payment-return handling
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
}

function GuestFields({ form, set, t }) {
  return (
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
    </Grid>
  )
}

async function submitHoldFlow({ draft, form, navigate }) {
  const hold = await holdBooking({
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
  })
  const bookingId = hold.booking_id || hold.id
  const holdToken = hold.hold_token
  persistGuestDraft(draft, form, bookingId, holdToken)

  const next = navigateAfterHold(navigate, {
    hold, bookingId, holdToken, paymentMode: form.payment_mode,
  })
  if (next !== 'confirm_hotel') return

  const confirmed = await confirmPayAtHotel({ bookingId, holdToken, form })
  const id = confirmed.booking_id || confirmed.id || bookingId
  persistGuestDraft(draft, form, id, holdToken)
  navigate(confirmationPath(id, holdToken))
}

function GuestForm({ draft }) {
  const navigate = useNavigate()
  const { t } = useBookingT()
  const [form, setForm] = useState({
    guest_first_name: draft.guest_first_name || '',
    guest_last_name: draft.guest_last_name || '',
    guest_email: draft.guest_email || '',
    guest_phone: draft.guest_phone || '',
    special_requests: draft.special_requests || '',
    payment_mode: draft.payment_mode || 'deposit',
  })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  usePaymentReturnConfirm({ draft, form, setError, setSubmitting, t })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await submitHoldFlow({ draft, form, navigate })
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
        <GuestFields form={form} set={set} t={t} />
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
          <Button onClick={() => navigate(-1)}>{t('back')}</Button>
          <Button type="submit" variant="contained" disabled={submitting} sx={{ minWidth: 160 }}>
            {submitting ? t('confirming') : t('confirmBooking')}
          </Button>
        </Box>
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
