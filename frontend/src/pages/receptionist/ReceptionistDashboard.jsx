import React from 'react'
import { Grid, Box } from '@mui/material'
import {
  Login as ArrivalsIcon,
  Logout as DeparturesIcon,
  People,
  Hotel,
  MeetingRoom,
  Add,
  ViewTimeline,
  EventNote,
  HotelOutlined,
  CleaningServices,
  PersonOutline,
} from '@mui/icons-material'
import { useGetDashboardStatsQuery } from '../../features/dashboard/dashboardApi'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import PageHeader from '../../components/common/PageHeader'
import AppLayout from '../../components/layout/AppLayout'
import OpsKpiStrip from '../../components/dashboard/OpsKpiStrip'
import IconQuickActions from '../../components/dashboard/IconQuickActions'
import TodayPanel from '../../components/dashboard/TodayPanel'

const ACTIONS = [
  { label: 'New booking', icon: Add, path: '/admin/bookings/new', color: 'primary' },
  { label: 'Calendar', icon: ViewTimeline, path: '/receptionist/tape-chart', color: 'primary' },
  { label: 'Check-in', icon: HotelOutlined, path: '/receptionist/check-in', color: 'success' },
  { label: 'Reservations', icon: EventNote, path: '/receptionist/bookings', color: 'primary' },
  { label: 'Guests', icon: PersonOutline, path: '/receptionist/guests', color: 'secondary' },
  { label: 'Housekeeping', icon: CleaningServices, path: '/receptionist/housekeeping', color: 'warning' },
]

export default function ReceptionistDashboard() {
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
        hint: stats.pending_arrivals != null ? `${stats.pending_arrivals} remaining` : undefined,
        icon: ArrivalsIcon,
        accent: 'success.main',
      },
      {
        label: 'Departures',
        value: stats.departures_today ?? stats.checkouts_today,
        hint: stats.pending_departures != null ? `${stats.pending_departures} remaining` : undefined,
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
        label: 'Stayovers',
        value: stats.stayovers,
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
        label: 'Occupancy',
        value: stats.occupancy_rate != null ? `${stats.occupancy_rate}%` : '—',
        icon: Hotel,
        accent: 'primary.dark',
      },
    ]
    : []

  return (
    <AppLayout>
      <PageHeader
        title="Front desk"
        subtitle={`${todayLabel} — what needs action now`}
      />

      {isLoading && <LoadingSpinner />}
      {error && <ErrorAlert error={error} title="Failed to load dashboard" />}

      {stats && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <IconQuickActions actions={ACTIONS} />
          <OpsKpiStrip items={kpis} />
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TodayPanel
                title="Arrivals"
                count={stats.arrivals_today ?? stats.checkins_today}
                pending={stats.pending_arrivals}
                description="Check guests in and assign rooms from the calendar if needed."
                ctaLabel="Check in"
                ctaPath="/receptionist/check-in"
                accent="success.main"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TodayPanel
                title="Departures"
                count={stats.departures_today ?? stats.checkouts_today}
                pending={stats.pending_departures}
                description="Complete check-out and release rooms to housekeeping."
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
