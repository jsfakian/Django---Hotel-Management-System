import React from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Chip,
  Button,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { EventNote, Receipt } from '@mui/icons-material'
import { selectCurrentUser } from '../../features/auth/authSlice'
import { useGetBookingsQuery } from '../../features/bookings/bookingsApi'
import LoadingSpinner from '../../components/common/LoadingSpinner'
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

export default function GuestDashboard() {
  const navigate = useNavigate()
  const user = useSelector(selectCurrentUser)
  const { data, isLoading } = useGetBookingsQuery({ status: 'confirmed,checked_in', limit: 3 })

  const upcomingBookings = data?.results ?? (Array.isArray(data) ? data.slice(0, 3) : [])

  return (
    <AppLayout>
      {/* Welcome card */}
      <Card sx={{ mb: 3, background: 'linear-gradient(135deg, #1565C0 0%, #1E88E5 100%)', color: 'white' }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h5" fontWeight={700}>
            Welcome back, {user?.username || 'Guest'}!
          </Typography>
          <Typography variant="body2" sx={{ opacity: 0.85, mt: 0.5 }}>
            Here is a summary of your upcoming stays at NEPHELE HMS.
          </Typography>
        </CardContent>
      </Card>

      {/* Upcoming bookings */}
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">Upcoming Bookings</Typography>
        <Button
          size="small"
          startIcon={<EventNote />}
          onClick={() => navigate('/guest/bookings')}
        >
          View All
        </Button>
      </Box>

      {isLoading && <LoadingSpinner />}

      {!isLoading && upcomingBookings.length === 0 && (
        <Card variant="outlined">
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <EventNote sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
            <Typography color="text.secondary">No upcoming bookings</Typography>
            <Typography variant="body2" color="text.disabled">
              Contact the hotel to make a reservation
            </Typography>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={2}>
        {upcomingBookings.map((booking) => (
          <Grid item xs={12} sm={6} md={4} key={booking.id}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="subtitle2" fontWeight={600}>
                    Booking #{booking.id}
                  </Typography>
                  <Chip
                    label={booking.status?.replace('_', ' ')}
                    size="small"
                    color={STATUS_COLORS[booking.status] || 'default'}
                    sx={{ textTransform: 'capitalize' }}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Room: {booking.room_number || booking.room?.number || booking.room || '—'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Check-in: {formatDate(booking.check_in_date)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Check-out: {formatDate(booking.check_out_date)}
                </Typography>
                {booking.total_price != null && (
                  <Typography variant="body2" fontWeight={500} sx={{ mt: 1 }}>
                    Total: €{Number(booking.total_price).toLocaleString()}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Quick links */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button
          variant="outlined"
          startIcon={<EventNote />}
          onClick={() => navigate('/guest/bookings')}
        >
          My Bookings
        </Button>
        <Button
          variant="outlined"
          startIcon={<Receipt />}
          onClick={() => navigate('/guest/invoices')}
        >
          My Invoices
        </Button>
      </Box>
    </AppLayout>
  )
}
