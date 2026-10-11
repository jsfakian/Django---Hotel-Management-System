import React from 'react'
import { Grid, Box } from '@mui/material'
import {
  EventNote,
  AttachMoney,
  Hotel,
  MeetingRoom,
  Login as ArrivalsIcon,
  Logout as DeparturesIcon,
  People,
  Add,
  ViewTimeline,
  CleaningServices,
  Payment,
  Settings,
  CloudSync,
} from '@mui/icons-material'
import { useGetDashboardStatsQuery } from '../../features/dashboard/dashboardApi'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import PageHeader from '../../components/common/PageHeader'
import EmptyState from '../../components/common/EmptyState'
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
  { label: 'Reservations', icon: EventNote, path: '/admin/bookings', color: 'primary' },
  { label: 'Housekeeping', icon: CleaningServices, path: '/receptionist/housekeeping', color: 'warning' },
  { label: 'Payments', icon: Payment, path: '/admin/payments', color: 'success' },
  { label: 'Channels', icon: CloudSync, path: '/admin/channels', color: 'secondary' },
  { label: 'Settings', icon: Settings, path: '/admin/settings', color: 'inherit' },
]

function buildKpis(stats) {
  return [
    {
      label: 'Arrivals',
      value: stats.arrivals_today ?? stats.checkins_today,
      hint: stats.pending_arrivals != null ? `${stats.pending_arrivals} to check in` : undefined,
      icon: ArrivalsIcon,
      accent: 'success.main',
    },
    {
      label: 'Departures',
      value: stats.departures_today ?? stats.checkouts_today,
      hint: stats.pending_departures != null ? `${stats.pending_departures} to check out` : undefined,
      icon: DeparturesIcon,
      accent: 'warning.main',
    },
    {
      label: 'In-house',
      value: stats.in_house ?? stats.active_guests,
      icon: People,
      accent: 'primary.main',
    },
    {
      label: 'Occupancy',
      value: stats.occupancy_rate != null ? `${stats.occupancy_rate}%` : '—',
      hint: stats.occupied_rooms != null
        ? `${stats.occupied_rooms}/${stats.total_rooms || '—'} rooms`
        : undefined,
      icon: Hotel,
      accent: 'secondary.main',
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
  ]
}

export default function AdminDashboard() {
  const { data: stats, isLoading, error } = useGetDashboardStatsQuery()
  const todayLabel = stats?.as_of
    ? new Date(`${stats.as_of}T12:00:00`).toLocaleDateString(undefined, {
      weekday: 'long', day: 'numeric', month: 'short',
    })
    : 'Today'

  return (
    <AppLayout>
      <PageHeader
        title="Dashboard"
        subtitle={`${todayLabel} — arrivals, house status, and shortcuts`}
      />

      {isLoading && <LoadingSpinner />}
      {error && <ErrorAlert error={error} title="Failed to load dashboard stats" />}
      {!isLoading && !error && !stats && (
        <EmptyState
          title="No metrics yet"
          description="Dashboard totals appear once bookings and payments are flowing."
        />
      )}

      {stats && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <IconQuickActions actions={ACTIONS} />
          <OpsKpiStrip items={buildKpis(stats)} />
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TodayPanel
                title="Arrivals today"
                count={stats.arrivals_today ?? stats.checkins_today}
                pending={stats.pending_arrivals}
                description="Guests expected to check in. Use Calendar or Check-in to place rooms."
                ctaLabel="Go to check-in"
                ctaPath="/receptionist/check-in"
                accent="success.main"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TodayPanel
                title="Departures today"
                count={stats.departures_today ?? stats.checkouts_today}
                pending={stats.pending_departures}
                description="Stays ending today. Clear folios and mark rooms for housekeeping."
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
