import React, { useEffect, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { Alert, Box, Button, CircularProgress, Typography, Grid } from '@mui/material'
import BookingShell from './BookingShell'
import { useBookingT } from './bookingLang'
import { clearBookingDraft, getConfirmation, loadBookingDraft } from '../../../features/public/publicBookingApi'

function Detail({ label, value }) {
  return (
    <Grid item xs={12} sm={6}>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
      <Typography>{value || '—'}</Typography>
    </Grid>
  )
}

function pick(primary, fallback, key, defaultValue) {
  return primary?.[key] ?? fallback?.[key] ?? defaultValue
}

function ConfirmationBody({ id, data, draft, error }) {
  const { t } = useBookingT()
  const confNo = pick(data, null, 'confirmation_number') || pick(data, null, 'id', id)
  const total = pick(data, draft, 'total')
  const fields = [
    [t('status'), pick(data, null, 'status', 'confirmed')],
    [t('email'), pick(data, draft, 'guest_email')],
    [t('checkIn'), pick(data, draft, 'check_in')],
    [t('checkOut'), pick(data, draft, 'check_out')],
    [t('room'), pick(data, draft, 'room_type_name')],
    [t('total'), total != null ? `€${Number(total).toFixed(2)}` : null],
  ]
  return (
    <>
      <Typography variant="h5" sx={{ mb: 1, fontFamily: '"Fraunces", Georgia, serif' }}>
        {t('confirmTitle')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t('confirmationHash')} #{confNo}
      </Typography>
      {error && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {t('confirmLocalSummary')} — {error}
        </Alert>
      )}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {fields.map(([label, value]) => (
          <Detail key={label} label={label} value={value} />
        ))}
      </Grid>
    </>
  )
}

function fallbackFromDraft(id, fallback) {
  return {
    id,
    status: 'confirmed',
    check_in: fallback?.check_in,
    check_out: fallback?.check_out,
    total: fallback?.total,
    guest_email: fallback?.guest_email,
    room_type_name: fallback?.room_type_name,
  }
}

function ConfirmActions({ id, clientSecret }) {
  const navigate = useNavigate()
  const { t } = useBookingT()
  return (
    <>
      {clientSecret && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {t('stripeCompleteHint')}
        </Alert>
      )}
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <Button variant="contained" onClick={() => navigate('/landing')}>
          {t('backToNephele')}
        </Button>
        <Button
          variant="outlined"
          onClick={() => navigate(`/book/manage?id=${encodeURIComponent(id)}`)}
        >
          {t('manageHold')}
        </Button>
      </Box>
    </>
  )
}

export default function BookingConfirmPage() {
  const { id } = useParams()
  const location = useLocation()
  const draft = loadBookingDraft()
  const clientSecret = location.state?.client_secret
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    const fallback = loadBookingDraft()
    async function run() {
      setLoading(true)
      try {
        const conf = await getConfirmation(id)
        if (!cancelled) {
          setData(conf)
          clearBookingDraft()
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Could not load confirmation')
          setData(fallbackFromDraft(id, fallback))
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [id])

  return (
    <BookingShell subtitleKey="confirmSubtitle">
      {loading && <Box sx={{ py: 4, textAlign: 'center' }}><CircularProgress /></Box>}
      {!loading && (
        <>
          <ConfirmationBody id={id} data={data} draft={draft} error={error} />
          <ConfirmActions id={id} clientSecret={clientSecret} />
        </>
      )}
    </BookingShell>
  )
}
