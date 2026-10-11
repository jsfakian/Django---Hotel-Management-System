import React from 'react'
import { Grid, Box } from '@mui/material'
import {
  EventNote,
  AttachMoney,
  Hotel,
  MeetingRoom,
  Login as ArrivalsIcon,
  Logout as DeparturesIcon,
  TrendingUp,
  Add,
  ViewTimeline,
  Payment,
  BarChart,
  Settings,
} from '@mui/icons-material'
import { useGetDashboardStatsQuery } from '../../features/dashboard/dashboardApi'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import PageHeader from '../../components/common/PageHeader'
import AppLayout from '../../components/layout/AppLayout'
import OpsKpiStrip from '../../components/dashboard/OpsKpiStrip'
import IconQuickActions from '../../components/dashboard/IconQuickActions'
import TodayPanel from '../../components/dashboard/TodayPanel'

function formatEur(n) {
  if (n == null) return '—'
  return `€${Number(n).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
}

const ACTIONS = [
  { label: 'New booking', icon: Add, path: '/admin/bookings/new', color: 'primary' },
  { label: 'Calendar', icon: ViewTimeline, path: '/receptionist/tape-chart', color: 'primary' },
  { label: 'Reservations', icon: EventNote, path: '/manager/bookings', color: 'primary' },
  { label: 'Payments', icon: Payment, path: '/admin/payments', color: 'success' },
  { label: 'Reports', icon: BarChart, path: '/manager/analytics', color: 'secondary' },
  { label: 'Settings', icon: Settings, path: '/manager/settings', color: 'inherit' },
]

export default function ManagerDashboard() {
  const { data: stats, isLoading, error } = useGetDashboardStatsQuery()
  const todayLabel = stats?.as_of
    ? new Date(`${stats.as_of}T12:00:00`).toLocaleDateString(undefined, {
      weekday: 'long', day: 'numeric', month: 'short',
    })
    : 'Today'

  const kpis = stats
    ? [
      {
        label: 'Arrivals',
        value: stats.arrivals_today ?? stats.checkins_today,
        icon: ArrivalsIcon,
        accent: 'success.main',
      },
      {
        label: 'Departures',
        value: stats.departures_today ?? stats.checkouts_today,
        icon: DeparturesIcon,
        accent: 'warning.main',
      },
      {
        label: 'Occupancy',
        value: stats.occupancy_rate != null ? `${stats.occupancy_rate}%` : '—',
        hint: stats.occupied_rooms != null
          ? `${stats.occupied_rooms} occupied`
          : undefined,
        icon: Hotel,
        accent: 'primary.main',
      },
      {
        label: 'Available',
        value: stats.available_rooms,
        icon: MeetingRoom,
        accent: 'info.main',
      },
      {
        label: 'Revenue MTD',
        value: formatEur(stats.revenue_mtd ?? stats.total_revenue),
        icon: AttachMoney,
        accent: 'success.dark',
      },
      {
        label: 'Bookings',
        value: stats.total_bookings,
        icon: TrendingUp,
        accent: 'secondary.main',
      },
    ]
    : []

  return (
    <AppLayout>
      <PageHeader
        title="Dashboard"
        subtitle={`${todayLabel} — property performance at a glance`}
      />

      {isLoading && <LoadingSpinner />}
      {error && <ErrorAlert error={error} title="Failed to load dashboard stats" />}

      {stats && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <IconQuickActions actions={ACTIONS} />
          <OpsKpiStrip items={kpis} />
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TodayPanel
                title="Arrivals today"
                count={stats.arrivals_today ?? stats.checkins_today}
                pending={stats.pending_arrivals}
                description="Expected check-ins across the property."
                ctaLabel="Open reservations"
                ctaPath="/manager/bookings"
                accent="success.main"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TodayPanel
                title="Departures today"
                count={stats.departures_today ?? stats.checkouts_today}
                pending={stats.pending_departures}
                description="Rooms freeing up — watch housekeeping turnaround."
                ctaLabel="Open calendar"
                ctaPath="/receptionist/tape-chart"
                accent="warning.main"
              />
            </Grid>
          </Grid>
        </Box>
      )}
    </AppLayout>
  )
}
