import React, { useState } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  Divider,
  CircularProgress,
  Alert,
} from '@mui/material'
import { Search, Login as CheckInIcon, Logout as CheckOutIcon } from '@mui/icons-material'
import { useGetBookingQuery, useCheckInMutation, useCheckOutMutation } from '../../features/bookings/bookingsApi'
import ErrorAlert from '../../components/common/ErrorAlert'
import AppLayout from '../../components/layout/AppLayout'

const STATUS_COLORS = {
  confirmed: 'success',
  pending: 'warning',
  checked_in: 'info',
  checked_out: 'default',
  cancelled: 'error',
}

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export default function CheckInPage() {
  const [bookingId, setBookingId] = useState('')
  const [searchId, setSearchId] = useState(null)
  const [successMsg, setSuccessMsg] = useState('')

  const {
    data: booking,
    isLoading: loadingBooking,
    error: bookingError,
  } = useGetBookingQuery(searchId, { skip: !searchId })

  const [checkIn, { isLoading: checkingIn, error: checkInError }] = useCheckInMutation()
  const [checkOut, { isLoading: checkingOut, error: checkOutError }] = useCheckOutMutation()

  const handleSearch = (e) => {
    e.preventDefault()
    setSuccessMsg('')
    const id = parseInt(bookingId, 10)
    if (id) setSearchId(id)
  }

  const handleCheckIn = async () => {
    try {
      await checkIn(booking.id).unwrap()
      setSuccessMsg(`Booking #${booking.id} checked in successfully.`)
    } catch {
      // handled by RTK error state
    }
  }

  const handleCheckOut = async () => {
    try {
      await checkOut(booking.id).unwrap()
      setSuccessMsg(`Booking #${booking.id} checked out successfully.`)
    } catch {
      // handled by RTK error state
    }
  }

  return (
    <AppLayout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5">Check-In / Check-Out</Typography>
        <Typography variant="body2" color="text.secondary">
          Look up a booking by ID and process check-in or check-out
        </Typography>
      </Box>

      {/* Search form */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box component="form" onSubmit={handleSearch} sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="Booking ID"
              value={bookingId}
              onChange={(e) => setBookingId(e.target.value)}
              size="small"
              type="number"
              sx={{ width: 200 }}
              required
            />
            <Button type="submit" variant="contained" startIcon={<Search />}>
              Look Up
            </Button>
          </Box>
        </CardContent>
      </Card>

      {loadingBooking && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {bookingError && <ErrorAlert error={bookingError} title="Booking not found" />}
      {checkInError && <ErrorAlert error={checkInError} title="Check-in failed" />}
      {checkOutError && <ErrorAlert error={checkOutError} title="Check-out failed" />}
      {successMsg && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {successMsg}
        </Alert>
      )}

      {booking && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Booking #{booking.id}</Typography>
              <Chip
                label={booking.status?.replace('_', ' ')}
                color={STATUS_COLORS[booking.status] || 'default'}
                sx={{ textTransform: 'capitalize' }}
              />
            </Box>
            <Divider sx={{ mb: 2 }} />

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">Guest</Typography>
                <Typography variant="body1" fontWeight={500}>
                  {booking.guest_name || booking.guest?.full_name || booking.guest?.username || '—'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">Room</Typography>
                <Typography variant="body1" fontWeight={500}>
                  {booking.room_number || booking.room?.number || booking.room || '—'}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">Check-in Date</Typography>
                <Typography variant="body1" fontWeight={500}>
                  {formatDate(booking.check_in_date)}
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">Check-out Date</Typography>
                <Typography variant="body1" fontWeight={500}>
                  {formatDate(booking.check_out_date)}
                </Typography>
              </Grid>
              {booking.total_price != null && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">Total Price</Typography>
                  <Typography variant="body1" fontWeight={500}>
                    €{Number(booking.total_price).toLocaleString()}
                  </Typography>
                </Grid>
              )}
            </Grid>

            <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
              {booking.status === 'confirmed' && (
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<CheckInIcon />}
                  disabled={checkingIn}
                  onClick={handleCheckIn}
                >
                  {checkingIn ? <CircularProgress size={20} color="inherit" /> : 'Confirm Check-In'}
                </Button>
              )}
              {booking.status === 'checked_in' && (
                <Button
                  variant="contained"
                  color="warning"
                  startIcon={<CheckOutIcon />}
                  disabled={checkingOut}
                  onClick={handleCheckOut}
                >
                  {checkingOut ? <CircularProgress size={20} color="inherit" /> : 'Confirm Check-Out'}
                </Button>
              )}
              {booking.status !== 'confirmed' && booking.status !== 'checked_in' && (
                <Typography variant="body2" color="text.secondary">
                  No actions available for status: {booking.status}
                </Typography>
              )}
            </Box>
          </CardContent>
        </Card>
      )}
    </AppLayout>
  )
}
