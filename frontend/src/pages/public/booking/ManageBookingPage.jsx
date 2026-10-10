import React, { useState } from 'react'
import { Link as RouterLink, useSearchParams } from 'react-router-dom'
import {
  Alert, Box, Button, Grid, Link, TextField, Typography,
} from '@mui/material'
import BookingShell from './BookingShell'
import { useBookingT } from './bookingLang'
import {
  cancelHold,
  getConfirmation,
  modifyHold,
} from '../../../features/public/publicBookingApi'

function LookupForm({ form, setForm, onLookup, loading }) {
  const { t } = useBookingT()
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
  return (
    <Box component="form" onSubmit={onLookup}>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={4}>
          <TextField
            fullWidth
            required
            label={t('holdId')}
            name="booking_id"
            value={form.booking_id}
            onChange={set('booking_id')}
          />
        </Grid>
        <Grid item xs={12} sm={5}>
          <TextField
            fullWidth
            type="email"
            label={t('emailOptional')}
            name="email"
            value={form.email}
            onChange={set('email')}
          />
        </Grid>
        <Grid item xs={12} sm={3} sx={{ display: 'flex', alignItems: 'center' }}>
          <Button type="submit" variant="contained" fullWidth disabled={loading}>
            {loading ? t('lookingUp') : t('lookUp')}
          </Button>
        </Grid>
      </Grid>
    </Box>
  )
}

function ModifyForm({ form, setForm, onSubmit, busy }) {
  const { t } = useBookingT()
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
  return (
    <Box component="form" onSubmit={onSubmit} sx={{ mt: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>{t('modifyHold')}</Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={4}>
          <TextField
            fullWidth
            type="date"
            label={t('checkIn')}
            InputLabelProps={{ shrink: true }}
            value={form.check_in}
            onChange={set('check_in')}
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <TextField
            fullWidth
            type="date"
            label={t('checkOut')}
            InputLabelProps={{ shrink: true }}
            value={form.check_out}
            onChange={set('check_out')}
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <TextField
            fullWidth
            type="number"
            label={t('adults')}
            inputProps={{ min: 1 }}
            value={form.adults}
            onChange={set('adults')}
          />
        </Grid>
        <Grid item xs={12}>
          <Button type="submit" variant="outlined" disabled={busy}>
            {busy ? t('updating') : t('updateHold')}
          </Button>
        </Grid>
      </Grid>
    </Box>
  )
}

function BookingSummary({ booking }) {
  if (!booking) return null
  return (
    <Box sx={{ mt: 3, mb: 2 }}>
      <Typography variant="body2" color="text.secondary">
        #{booking.confirmation_number || booking.booking_id || booking.id}
        {' · '}
        {booking.status}
        {booking.guest_email ? ` · ${booking.guest_email}` : ''}
      </Typography>
      <Typography>
        {booking.check_in || booking.check_in_date || '—'}
        {' → '}
        {booking.check_out || booking.check_out_date || '—'}
      </Typography>
    </Box>
  )
}

async function lookupBooking(bookingId, email, t) {
  const conf = await getConfirmation(bookingId)
  if (email && conf.guest_email && conf.guest_email.toLowerCase() !== email.toLowerCase()) {
    throw new Error(t('emailMismatch'))
  }
  return conf
}

function ManageInner() {
  const { t } = useBookingT()
  const [params] = useSearchParams()
  const [lookup, setLookup] = useState({
    booking_id: params.get('id') || '',
    email: params.get('email') || '',
  })
  const [booking, setBooking] = useState(null)
  const [modify, setModify] = useState({ check_in: '', check_out: '', adults: 1 })
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)

  const handleLookup = async (e) => {
    e.preventDefault()
    setError('')
    setMsg('')
    setBusy(true)
    try {
      const conf = await lookupBooking(lookup.booking_id, lookup.email, t)
      setBooking(conf)
      setModify({
        check_in: conf.check_in || conf.check_in_date || '',
        check_out: conf.check_out || conf.check_out_date || '',
        adults: conf.adults || 1,
      })
    } catch (err) {
      setBooking(null)
      setError(err.message || t('lookupFailed'))
    } finally {
      setBusy(false)
    }
  }

  const handleCancel = async () => {
    if (!booking) return
    setError('')
    setMsg('')
    setBusy(true)
    try {
      const id = booking.booking_id || booking.id
      const result = await cancelHold(id)
      setMsg(`#${result.booking_id} ${t('bookingCancelled')}`)
      setBooking({ ...booking, status: result.status })
    } catch (err) {
      setError(err.data?.error || err.message || t('cancelFailed'))
    } finally {
      setBusy(false)
    }
  }

  const handleModify = async (e) => {
    e.preventDefault()
    if (!booking) return
    setError('')
    setMsg('')
    setBusy(true)
    try {
      const id = booking.booking_id || booking.id
      const payload = {
        check_in: modify.check_in || undefined,
        check_out: modify.check_out || undefined,
        adults: Number(modify.adults) || undefined,
      }
      const updated = await modifyHold(id, payload)
      setBooking({ ...booking, ...updated })
      setMsg(t('holdUpdated'))
    } catch (err) {
      setError(err.data?.error || err.message || t('modifyFailed'))
    } finally {
      setBusy(false)
    }
  }

  const canEdit = booking && (booking.status === 'held' || booking.status === 'pending')

  return (
    <>
      <Typography variant="h6" sx={{ mb: 2, fontFamily: '"Fraunces", Georgia, serif' }}>
        {t('manageTitle')}
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {msg && <Alert severity="success" sx={{ mb: 2 }}>{msg}</Alert>}
      <LookupForm form={lookup} setForm={setLookup} onLookup={handleLookup} loading={busy && !booking} />
      <BookingSummary booking={booking} />
      {canEdit && (
        <>
          <Button color="error" variant="outlined" onClick={handleCancel} disabled={busy} sx={{ mr: 1 }}>
            {t('cancelHold')}
          </Button>
          <ModifyForm form={modify} setForm={setModify} onSubmit={handleModify} busy={busy} />
        </>
      )}
      {booking && !canEdit && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {t('onlyHeldInfo')}
        </Alert>
      )}
      <Box sx={{ mt: 3 }}>
        <Link component={RouterLink} to="/book">{t('newSearch')}</Link>
      </Box>
    </>
  )
}

export default function ManageBookingPage() {
  return (
    <BookingShell subtitleKey="manageSubtitle">
      <ManageInner />
    </BookingShell>
  )
}
