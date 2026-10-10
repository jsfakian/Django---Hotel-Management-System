import React from 'react'
import { Box, Typography, Chip, Card, CardContent, Grid } from '@mui/material'
import { EventNote } from '@mui/icons-material'
import { useGetBookingsQuery } from '../../features/bookings/bookingsApi'
import ErrorAlert from '../../components/common/ErrorAlert'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import EmptyState from '../../components/common/EmptyState'
import GuestLayout from '../../components/layout/GuestLayout'

const STATUS_LABELS = {
  confirmed: 'Confirmed',
  pending: 'Pending',
  checked_in: 'Checked in',
  checked_out: 'Checked out',
  cancelled: 'Cancelled',
}

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

export default function MyBookingsPage() {
  const { data, isLoading, error } = useGetBookingsQuery({})
  const rows = data?.results ?? (Array.isArray(data) ? data : [])

  return (
    <GuestLayout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontFamily: '"Fraunces", Georgia, serif' }}>
          Your stays
        </Typography>
        <Typography variant="body2" color="text.secondary">
          A timeline of reservations at Nephele properties
        </Typography>
      </Box>

      {error && <ErrorAlert error={error} title="Failed to load bookings" />}
      {isLoading ? (
        <LoadingSpinner />
      ) : rows.length === 0 ? (
        <EmptyState
          title="No reservations yet"
          description="When you book a stay, it will appear here with dates and status."
          icon={<EventNote fontSize="large" />}
        />
      ) : (
        <Grid container spacing={2}>
          {rows.map((booking) => (
            <Grid item xs={12} key={booking.id}>
              <Card>
                <CardContent
                  sx={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: 2,
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <Box>
                    <Typography variant="overline" color="text.secondary">
                      Stay #{booking.id}
                    </Typography>
                    <Typography variant="h6">
                      {formatDate(booking.check_in_date)} → {formatDate(booking.check_out_date)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Room {booking.room_number || booking.room?.number || booking.room || '—'}
                      {booking.total_price != null
                        ? ` · €${Number(booking.total_price).toLocaleString()}`
                        : ''}
                    </Typography>
                  </Box>
                  <Chip
                    label={STATUS_LABELS[booking.status] || booking.status?.replace('_', ' ')}
                    color={STATUS_COLORS[booking.status] || 'default'}
                    sx={{ textTransform: 'capitalize', fontWeight: 600 }}
                  />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </GuestLayout>
  )
}
