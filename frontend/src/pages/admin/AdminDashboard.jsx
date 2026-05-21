import React from 'react'
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
} from '@mui/material'
import {
  EventNote,
  AttachMoney,
  Hotel,
  People,
} from '@mui/icons-material'
import { useGetDashboardStatsQuery } from '../../features/dashboard/dashboardApi'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import AppLayout from '../../components/layout/AppLayout'

function StatCard({ title, value, icon: Icon, color }) {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" fontWeight={700}>
              {value ?? '—'}
            </Typography>
          </Box>
          <Box
            sx={{
              width: 56,
              height: 56,
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: `${color}.light`,
            }}
          >
            <Icon sx={{ color: `${color}.main`, fontSize: 28 }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  )
}

export default function AdminDashboard() {
  const { data: stats, isLoading, error } = useGetDashboardStatsQuery()

  return (
    <AppLayout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5">Admin Dashboard</Typography>
        <Typography variant="body2" color="text.secondary">
          Overview of hotel operations
        </Typography>
      </Box>

      {isLoading && <LoadingSpinner />}
      {error && <ErrorAlert error={error} title="Failed to load dashboard stats" />}

      {stats && (
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} lg={3}>
            <StatCard
              title="Total Bookings"
              value={stats.total_bookings}
              icon={EventNote}
              color="primary"
            />
          </Grid>
          <Grid item xs={12} sm={6} lg={3}>
            <StatCard
              title="Revenue (MTD)"
              value={
                stats.revenue_mtd != null
                  ? `€${Number(stats.revenue_mtd).toLocaleString()}`
                  : '—'
              }
              icon={AttachMoney}
              color="success"
            />
          </Grid>
          <Grid item xs={12} sm={6} lg={3}>
            <StatCard
              title="Occupancy Rate"
              value={
                stats.occupancy_rate != null
                  ? `${stats.occupancy_rate}%`
                  : '—'
              }
              icon={Hotel}
              color="warning"
            />
          </Grid>
          <Grid item xs={12} sm={6} lg={3}>
            <StatCard
              title="Active Guests"
              value={stats.active_guests}
              icon={People}
              color="secondary"
            />
          </Grid>
        </Grid>
      )}
    </AppLayout>
  )
}
