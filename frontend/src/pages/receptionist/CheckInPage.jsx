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
import PageHeader from '../../components/common/PageHeader'
import EmptyState from '../../components/common/EmptyState'
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

const DASH = '—'

function Field({ label, children }) {
  return (
    <Grid item xs={12} sm={6}>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
      <Typography variant="body1" fontWeight={500}>{children}</Typography>
    </Grid>
  )
}

const guestLabel = (b) => b.guest_name || b.guest?.full_name || b.guest?.username || DASH
const roomLabel = (b) => b.room_number || b.room?.number || b.room || DASH

function BookingDetails({ booking }) {
  return (
    <Grid container spacing={2}>
      <Field label="Guest">{guestLabel(booking)}</Field>
      <Field label="Room">{roomLabel(booking)}</Field>
      <Field label="Check-in Date">{formatDate(booking.check_in_date)}</Field>
      <Field label="Check-out Date">{formatDate(booking.check_out_date)}</Field>
      {booking.total_price != null && (
        <Field label="Total Price">€{Number(booking.total_price).toLocaleString()}</Field>
      )}
    </Grid>
  )
}

function ActionButton({ color, icon, busy, onClick, label }) {
  return (
    <Button variant="contained" color={color} startIcon={icon} disabled={busy} onClick={onClick}>
      {busy ? <CircularProgress size={20} color="inherit" /> : label}
    </Button>
  )
}

function BookingActions({ booking, checkingIn, checkingOut, onCheckIn, onCheckOut }) {
  const { status } = booking
  return (
    <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
      {status === 'confirmed' && (
        <ActionButton color="success" icon={<CheckInIcon />} busy={checkingIn} onClick={onCheckIn} label="Confirm Check-In" />
      )}
      {status === 'checked_in' && (
        <ActionButton color="warning" icon={<CheckOutIcon />} busy={checkingOut} onClick={onCheckOut} label="Confirm Check-Out" />
      )}
      {status !== 'confirmed' && status !== 'checked_in' && (
        <Typography variant="body2" color="text.secondary">
          No actions available for status: {status}
        </Typography>
      )}
    </Box>
  )
}

function BookingCard({ booking, ...actions }) {
  return (
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
        <BookingDetails booking={booking} />
        <BookingActions booking={booking} {...actions} />
      </CardContent>
    </Card>
  )
}

function LookupForm({ value, onChange, onSubmit }) {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box component="form" onSubmit={onSubmit} sx={{ display: 'flex', gap: 2 }}>
          <TextField
            label="Booking ID"
            value={value}
            onChange={(e) => onChange(e.target.value)}
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
  )
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
      <PageHeader
        title="Check-In / Check-Out"
        subtitle="Look up a booking by ID to arrive or depart a guest"
      />

      <LookupForm value={bookingId} onChange={setBookingId} onSubmit={handleSearch} />

      {!searchId && !loadingBooking && (
        <EmptyState
          title="Ready for the next arrival"
          description="Enter a booking ID above to check a guest in or out."
          icon={<Search fontSize="large" />}
        />
      )}

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
        <BookingCard
          booking={booking}
          checkingIn={checkingIn}
          checkingOut={checkingOut}
          onCheckIn={handleCheckIn}
          onCheckOut={handleCheckOut}
        />
      )}
    </AppLayout>
  )
}
