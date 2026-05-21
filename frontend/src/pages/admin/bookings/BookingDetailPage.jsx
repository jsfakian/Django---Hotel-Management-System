import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, Paper, Typography, Grid, Chip, Dialog, DialogTitle, DialogContent, DialogActions, Alert } from '@mui/material'
import { ArrowBack, Edit } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetBookingQuery, useCheckInMutation, useCheckOutMutation, useCancelBookingMutation } from '../../../features/bookings/bookingsApi'

const STATUS_COLORS = { pending: 'warning', confirmed: 'info', checked_in: 'success', checked_out: 'default', cancelled: 'error' }

export default function BookingDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [cancelOpen, setCancelOpen] = useState(false)
  const [actionMsg, setActionMsg] = useState('')
  const { data: booking, isLoading, error } = useGetBookingQuery(id)
  const [checkIn, { isLoading: checkingIn }] = useCheckInMutation()
  const [checkOut, { isLoading: checkingOut }] = useCheckOutMutation()
  const [cancel, { isLoading: cancelling }] = useCancelBookingMutation()

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!booking) return null

  const doAction = async (fn) => {
    const result = await fn(id)
    if (!result.error) setActionMsg('Action completed successfully.')
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/admin/bookings')}>Back</Button>
        <Button variant="outlined" startIcon={<Edit />} onClick={() => navigate(`/admin/bookings/${id}/edit`)}>Edit</Button>
      </Box>
      {actionMsg && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setActionMsg('')}>{actionMsg}</Alert>}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Typography variant="h5">Booking #{booking.id}</Typography>
          <Chip label={booking.status} color={STATUS_COLORS[booking.status] || 'default'} />
        </Box>
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[
            ['Guest', booking.guest_name || booking.guest],
            ['Room', booking.room_number || booking.room],
            ['Property', booking.property_name || booking.property],
            ['Check-in', booking.check_in_date],
            ['Check-out', booking.check_out_date],
            ['Nights', booking.nights],
            ['Total Price', `€${Number(booking.total_price || 0).toFixed(2)}`],
            ['Adults', booking.adults],
            ['Children', booking.children],
          ].map(([label, val]) => (
            <Grid item xs={12} sm={6} md={4} key={label}>
              <Typography variant="caption" color="text.secondary">{label}</Typography>
              <Typography variant="body1">{val || '—'}</Typography>
            </Grid>
          ))}
          {booking.notes && <Grid item xs={12}><Typography variant="caption" color="text.secondary">Notes</Typography><Typography variant="body2">{booking.notes}</Typography></Grid>}
          {booking.special_requests && <Grid item xs={12}><Typography variant="caption" color="text.secondary">Special Requests</Typography><Typography variant="body2">{booking.special_requests}</Typography></Grid>}
        </Grid>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          {booking.status === 'confirmed' && <Button variant="contained" color="success" onClick={() => doAction(checkIn)} disabled={checkingIn}>Check In</Button>}
          {booking.status === 'checked_in' && <Button variant="contained" color="primary" onClick={() => doAction(checkOut)} disabled={checkingOut}>Check Out</Button>}
          {['pending', 'confirmed'].includes(booking.status) && <Button variant="outlined" color="error" onClick={() => setCancelOpen(true)}>Cancel Booking</Button>}
        </Box>
      </Paper>
      <Dialog open={cancelOpen} onClose={() => setCancelOpen(false)}>
        <DialogTitle>Cancel Booking #{booking.id}?</DialogTitle>
        <DialogContent>This will cancel the booking. This cannot be undone.</DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelOpen(false)}>No</Button>
          <Button color="error" onClick={() => { doAction(cancel); setCancelOpen(false) }} disabled={cancelling}>Yes, Cancel</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
