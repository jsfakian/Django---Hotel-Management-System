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
import { EventNote, Receipt, RoomService, Shield } from '@mui/icons-material'
import { selectCurrentUser } from '../../features/auth/authSlice'
import { useGetBookingsQuery } from '../../features/bookings/bookingsApi'
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

const QUICK = [
  { label: 'My stays', path: '/guest/bookings', icon: <EventNote /> },
  { label: 'Invoices', path: '/guest/invoices', icon: <Receipt /> },
  { label: 'Room services', path: '/guest/room-services', icon: <RoomService /> },
  { label: 'Privacy & data', path: '/guest/privacy', icon: <Shield /> },
]

function WelcomeHero({ user, nextStay }) {
  const roomNumber = nextStay?.room_number || nextStay?.room?.number
  return (
    <Box
      sx={{
        mb: 4,
        p: { xs: 3, md: 4 },
        borderRadius: 3,
        color: 'common.white',
        background: 'linear-gradient(135deg, #084852 0%, #0B5F6B 55%, #1A7A88 100%)',
        animation: 'guestHeroIn 0.7s ease-out',
        '@keyframes guestHeroIn': {
          from: { opacity: 0, transform: 'translateY(10px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
      }}
    >
      <Typography variant="overline" sx={{ opacity: 0.85, letterSpacing: 1.5 }}>
        Your stay
      </Typography>
      <Typography variant="h3" sx={{ mb: 1, fontFamily: '"Fraunces", Georgia, serif' }}>
        Welcome, {user?.first_name || user?.username || 'guest'}
      </Typography>
      {nextStay ? (
        <>
          <Typography variant="body1" sx={{ opacity: 0.92, mb: 2, maxWidth: 520 }}>
            Next arrival {formatDate(nextStay.check_in_date)}
            {roomNumber ? ` · Room ${roomNumber}` : ''}
          </Typography>
          <Chip
            label={STATUS_LABELS[nextStay.status] || nextStay.status}
            color={STATUS_COLORS[nextStay.status] || 'default'}
            sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: 'common.white', fontWeight: 600 }}
          />
        </>
      ) : (
        <Typography variant="body1" sx={{ opacity: 0.92, maxWidth: 480 }}>
          When you have an upcoming reservation, it will appear here with everything you need for
          arrival.
        </Typography>
      )}
    </Box>
  )
}

function QuickLinks({ onNavigate }) {
  return (
    <>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Quick links
      </Typography>
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {QUICK.map(({ label, path, icon }) => (
          <Grid item xs={6} sm={3} key={path}>
            <Card
              sx={{
                cursor: 'pointer',
                height: '100%',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': { transform: 'translateY(-2px)', boxShadow: 3 },
              }}
              onClick={() => onNavigate(path)}
            >
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <Box sx={{ color: 'primary.main', mb: 1 }}>{icon}</Box>
                <Typography fontWeight={600}>{label}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </>
  )
}

function StayCard({ booking }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Chip
          size="small"
          label={STATUS_LABELS[booking.status] || booking.status}
          color={STATUS_COLORS[booking.status] || 'default'}
          sx={{ mb: 1.5, textTransform: 'capitalize' }}
        />
        <Typography variant="h6" sx={{ mb: 0.5 }}>
          {formatDate(booking.check_in_date)} → {formatDate(booking.check_out_date)}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Room {booking.room_number || booking.room?.number || booking.room || '—'}
        </Typography>
      </CardContent>
    </Card>
  )
}

function UpcomingStays({ bookings, isLoading, onNavigate }) {
  if (isLoading) return <LoadingSpinner />
  if (bookings.length === 0) {
    return (
      <EmptyState
        title="No upcoming stays"
        description="Confirmed and in-house reservations will show here."
        actionLabel="Browse history"
        onAction={() => onNavigate('/guest/bookings')}
        icon={<EventNote fontSize="large" />}
      />
    )
  }
  return (
    <Grid container spacing={2}>
      {bookings.map((booking) => (
        <Grid item xs={12} md={4} key={booking.id}>
          <StayCard booking={booking} />
        </Grid>
      ))}
    </Grid>
  )
}

export default function GuestDashboard() {
  const navigate = useNavigate()
  const user = useSelector(selectCurrentUser)
  const { data, isLoading } = useGetBookingsQuery({
    status: 'confirmed,checked_in',
    limit: 3,
  })

  const upcomingBookings = data?.results ?? (Array.isArray(data) ? data.slice(0, 3) : [])

  return (
    <GuestLayout>
      <WelcomeHero user={user} nextStay={upcomingBookings[0]} />
      <QuickLinks onNavigate={navigate} />

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', mb: 2 }}>
        <Typography variant="h6">Upcoming stays</Typography>
        <Button size="small" onClick={() => navigate('/guest/bookings')}>
          View all
        </Button>
      </Box>

      <UpcomingStays bookings={upcomingBookings} isLoading={isLoading} onNavigate={navigate} />
    </GuestLayout>
  )
}
