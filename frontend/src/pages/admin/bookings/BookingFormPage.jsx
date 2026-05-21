import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, TextField, MenuItem, Select, FormControl, InputLabel, Paper, Typography, Grid } from '@mui/material'
import { ArrowBack, Save } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetBookingQuery, useCreateBookingMutation, useUpdateBookingMutation } from '../../../features/bookings/bookingsApi'
import { useGetGuestsQuery } from '../../../features/guests/guestsApi'
import { useGetRoomsQuery } from '../../../features/rooms/roomsApi'

export default function BookingFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const { data: booking } = useGetBookingQuery(id, { skip: !isEdit })
  const { data: guestsData } = useGetGuestsQuery()
  const { data: roomsData } = useGetRoomsQuery()
  const [createBooking, { isLoading: creating, error: createError }] = useCreateBookingMutation()
  const [updateBooking, { isLoading: updating, error: updateError }] = useUpdateBookingMutation()

  const guests = guestsData?.results || guestsData || []
  const rooms = roomsData?.results || roomsData || []
  const error = createError || updateError
  const isLoading = creating || updating

  const [form, setForm] = useState({ guest: '', room: '', check_in_date: '', check_out_date: '', status: 'pending', adults: 1, children: 0, notes: '', special_requests: '' })

  useEffect(() => {
    if (booking) setForm({ guest: booking.guest || '', room: booking.room || '', check_in_date: booking.check_in_date || '', check_out_date: booking.check_out_date || '', status: booking.status || 'pending', adults: booking.adults || 1, children: booking.children || 0, notes: booking.notes || '', special_requests: booking.special_requests || '' })
  }, [booking])

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = isEdit ? await updateBooking({ id, ...form }) : await createBooking(form)
    if (!result.error) navigate(isEdit ? `/admin/bookings/${id}` : '/admin/bookings')
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate(isEdit ? `/admin/bookings/${id}` : '/admin/bookings')}>Back</Button>
        <Typography variant="h5">{isEdit ? 'Edit Booking' : 'New Booking'}</Typography>
      </Box>
      {error && <ErrorAlert error={error} />}
      <Paper sx={{ p: 3 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Guest</InputLabel>
                <Select name="guest" value={form.guest} label="Guest" onChange={handleChange}>
                  {guests.map((g) => <MenuItem key={g.id} value={g.id}>{g.first_name} {g.last_name} — {g.email}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Room</InputLabel>
                <Select name="room" value={form.room} label="Room" onChange={handleChange}>
                  {rooms.map((r) => <MenuItem key={r.id} value={r.id}>Room {r.room_number} ({r.room_type})</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth required label="Check-in Date" name="check_in_date" type="date" InputLabelProps={{ shrink: true }} value={form.check_in_date} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth required label="Check-out Date" name="check_out_date" type="date" InputLabelProps={{ shrink: true }} value={form.check_out_date} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select name="status" value={form.status} label="Status" onChange={handleChange}>
                  {['pending', 'confirmed'].map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6} sm={4}><TextField fullWidth type="number" label="Adults" name="adults" value={form.adults} onChange={handleChange} inputProps={{ min: 1 }} /></Grid>
            <Grid item xs={6} sm={4}><TextField fullWidth type="number" label="Children" name="children" value={form.children} onChange={handleChange} inputProps={{ min: 0 }} /></Grid>
            <Grid item xs={12}><TextField fullWidth multiline rows={2} label="Notes" name="notes" value={form.notes} onChange={handleChange} /></Grid>
            <Grid item xs={12}><TextField fullWidth multiline rows={2} label="Special Requests" name="special_requests" value={form.special_requests} onChange={handleChange} /></Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Button type="submit" variant="contained" startIcon={<Save />} disabled={isLoading}>
              {isLoading ? 'Saving...' : 'Save Booking'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </AppLayout>
  )
}
