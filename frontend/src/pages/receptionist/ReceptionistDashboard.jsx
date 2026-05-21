import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Button,
} from '@mui/material'
import {
  Login as CheckInIcon,
  Logout as CheckOutIcon,
  Add,
  EventNote,
} from '@mui/icons-material'
import { useGetDashboardStatsQuery } from '../../features/dashboard/dashboardApi'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import AppLayout from '../../components/layout/AppLayout'

export default function ReceptionistDashboard() {
  const navigate = useNavigate()
  const { data: stats, isLoading, error } = useGetDashboardStatsQuery()

  return (
    <AppLayout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5">Reception Dashboard</Typography>
        <Typography variant="body2" color="text.secondary">
          Today's activity at a glance
        </Typography>
      </Box>

      {isLoading && <LoadingSpinner />}
      {error && <ErrorAlert error={error} title="Failed to load dashboard" />}

      {stats && (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 52,
                    height: 52,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: 'success.light',
                  }}
                >
                  <CheckInIcon sx={{ color: 'success.main', fontSize: 28 }} />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Check-ins Today
                  </Typography>
                  <Typography variant="h4" fontWeight={700}>
                    {stats.checkins_today ?? '—'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Card>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    width: 52,
                    height: 52,
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: 'warning.light',
                  }}
                >
                  <CheckOutIcon sx={{ color: 'warning.main', fontSize: 28 }} />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Check-outs Today
                  </Typography>
                  <Typography variant="h4" fontWeight={700}>
                    {stats.checkouts_today ?? '—'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Quick actions */}
      <Card>
        <CardContent>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            Quick Actions
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 1 }}>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => navigate('/receptionist/bookings')}
            >
              New Booking
            </Button>
            <Button
              variant="outlined"
              startIcon={<CheckInIcon />}
              onClick={() => navigate('/receptionist/check-in')}
            >
              Check In
            </Button>
            <Button
              variant="outlined"
              startIcon={<CheckOutIcon />}
              onClick={() => navigate('/receptionist/check-in')}
            >
              Check Out
            </Button>
            <Button
              variant="outlined"
              startIcon={<EventNote />}
              onClick={() => navigate('/receptionist/bookings')}
            >
              View All Bookings
            </Button>
          </Box>
        </CardContent>
      </Card>
    </AppLayout>
  )
}
