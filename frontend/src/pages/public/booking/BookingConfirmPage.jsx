import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Box, Button, CircularProgress, Typography, Grid } from '@mui/material'
import BookingShell from './BookingShell'
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
  const confNo = pick(data, null, 'confirmation_number') || pick(data, null, 'id', id)
  const total = pick(data, draft, 'total')
  const fields = [
    ['Status', pick(data, null, 'status', 'confirmed')],
    ['Email', pick(data, draft, 'guest_email')],
    ['Check-in', pick(data, draft, 'check_in')],
    ['Check-out', pick(data, draft, 'check_out')],
    ['Room', pick(data, draft, 'room_type_name')],
    ['Total', total != null ? `€${Number(total).toFixed(2)}` : null],
  ]
  return (
    <>
      <Typography variant="h5" sx={{ mb: 1, fontFamily: '"Fraunces", Georgia, serif' }}>
        Booking confirmed
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Confirmation #{confNo}
      </Typography>
      {error && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Showing local summary — {error}
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

export default function BookingConfirmPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const draft = loadBookingDraft()
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
    <BookingShell subtitle="Your reservation is held with care.">
      {loading && <Box sx={{ py: 4, textAlign: 'center' }}><CircularProgress /></Box>}
      {!loading && (
        <>
          <ConfirmationBody id={id} data={data} draft={draft} error={error} />
          <Button variant="contained" onClick={() => navigate('/landing')}>Back to Nephele</Button>
        </>
      )}
    </BookingShell>
  )
}
