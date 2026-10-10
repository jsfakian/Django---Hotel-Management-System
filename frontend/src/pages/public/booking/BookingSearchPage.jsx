import React, { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Box, Button, Grid, TextField, Typography, Alert } from '@mui/material'
import BookingShell from './BookingShell'
import { saveBookingDraft } from '../../../features/public/publicBookingApi'

function tomorrowIso() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}

function plusDaysIso(base, days) {
  const d = new Date(`${base}T00:00:00`)
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

export default function BookingSearchPage({ embedded = false }) {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [form, setForm] = useState({
    property_id: params.get('property_id') || '1',
    check_in: tomorrowIso(),
    check_out: plusDaysIso(tomorrowIso(), 2),
    adults: 2,
    children: 0,
  })
  const [error, setError] = useState('')

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')
    if (!form.property_id || !form.check_in || !form.check_out) {
      setError('Property and dates are required.')
      return
    }
    if (form.check_out <= form.check_in) {
      setError('Check-out must be after check-in.')
      return
    }
    const draft = {
      property_id: Number(form.property_id),
      check_in: form.check_in,
      check_out: form.check_out,
      adults: Number(form.adults) || 1,
      children: Number(form.children) || 0,
    }
    saveBookingDraft(draft)
    const params = new URLSearchParams({
      property_id: String(draft.property_id),
      check_in: draft.check_in,
      check_out: draft.check_out,
      adults: String(draft.adults),
      children: String(draft.children),
    })
    navigate(`/book/results?${params.toString()}`)
  }

  const body = (
    <>
      <Typography variant="h6" sx={{ mb: 2, fontFamily: '"Fraunces", Georgia, serif' }}>
        Search availability
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <Box component="form" onSubmit={handleSubmit}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <TextField fullWidth required label="Property ID" type="number" value={form.property_id} onChange={set('property_id')} />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField fullWidth required type="date" label="Check-in" InputLabelProps={{ shrink: true }} value={form.check_in} onChange={set('check_in')} />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField fullWidth required type="date" label="Check-out" InputLabelProps={{ shrink: true }} value={form.check_out} onChange={set('check_out')} />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField fullWidth label="Adults" type="number" inputProps={{ min: 1 }} value={form.adults} onChange={set('adults')} />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField fullWidth label="Children" type="number" inputProps={{ min: 0 }} value={form.children} onChange={set('children')} />
          </Grid>
          <Grid item xs={12}>
            <Button type="submit" variant="contained" color="primary" size="large" fullWidth={embedded}>
              Search stays
            </Button>
          </Grid>
        </Grid>
      </Box>
    </>
  )

  if (embedded) {
    return body
  }
  return (
    <BookingShell subtitle="Choose dates and guests — we will show open room types and rates.">
      {body}
    </BookingShell>
  )
}
