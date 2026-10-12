import React, { useState } from 'react'
import { Box, Grid, Card, CardContent, Typography, IconButton, Paper, List, ListItem, ListItemAvatar, ListItemText, Avatar, Chip, Divider, Tooltip } from '@mui/material'
import { Refresh } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import DataTable from '../../components/common/DataTable'
import { AnalyticsFilters, AnalyticsHeader } from '../../components/analytics/AnalyticsFilters'
import { useGetOperationalOverviewQuery } from '../../features/analytics/analyticsApi'

const ROOM_COLORS = { occupied: '#1565C0', available: '#2E7D32', cleaning: '#E65100', maintenance: '#B71C1C', reserved: '#6A1B9A', blocked: '#424242' }
const PRIORITY_COLORS = { urgent: 'error', high: 'error', medium: 'warning', low: 'success' }

const taskColumns = (showProperty) => [
  { field: 'title', headerName: 'Task', width: 220 },
  { field: 'employee_name', headerName: 'Employee', width: 160 },
  ...(showProperty ? [{ field: 'property_name', headerName: 'Property', width: 180 }] : []),
  { field: 'priority', headerName: 'Priority', width: 110, renderCell: ({ row }) => <Chip size="small" label={row.priority} color={PRIORITY_COLORS[row.priority] || 'default'} /> },
  { field: 'status', headerName: 'Status', width: 120 },
  { field: 'due_time', headerName: 'Due', width: 120 },
]

const STATUS_TILES = [
  ['Occupied', 'occupied', 'primary'], ['Available', 'available', 'success'], ['Cleaning', 'cleaning', 'warning'],
  ['Maintenance', 'maintenance', 'error'], ['Blocked', 'blocked', 'secondary'], ['Total', 'total', 'info'],
]

function StatusTiles({ status }) {
  return (
    <Grid container spacing={2} sx={{ mb: 4 }}>
      {STATUS_TILES.map(([label, key, color]) => (
        <Grid item xs={6} sm={4} md={2} key={label}>
          <Card><CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h4" fontWeight={700} color={`${color}.main`}>{status[key] || 0}</Typography>
            <Typography variant="body2" color="text.secondary">{label}</Typography>
          </CardContent></Card>
        </Grid>
      ))}
    </Grid>
  )
}

function GuestMovementList({ title, items, emptyText, avatarColor, showProperty }) {
  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <Typography variant="h6" gutterBottom>{title} ({items.length})</Typography>
      <Divider sx={{ mb: 1 }} />
      <List dense sx={{ maxHeight: 360, overflowY: 'auto' }}>{items.length ? items.map((c) => (
        <ListItem key={c.booking_id} secondaryAction={<Chip size="small" variant="outlined" label={c.status} />}>
          <ListItemAvatar><Avatar sx={{ bgcolor: avatarColor, width: 32, height: 32, fontSize: 14 }}>{(c.guest_name || 'G')[0]}</Avatar></ListItemAvatar>
          <ListItemText primary={c.guest_name} secondary={`Room ${c.room_number || '—'} · Booking #${c.booking_id}${showProperty && c.property_name ? ` · ${c.property_name}` : ''}`} />
        </ListItem>
      )) : <Typography color="text.secondary" variant="body2">{emptyText}</Typography>}</List>
    </Paper>
  )
}

function RoomGrid({ rooms }) {
  const groups = rooms.reduce((acc, r) => {
    const key = r.property_name || 'Rooms'
    ;(acc[key] = acc[key] || []).push(r)
    return acc
  }, {})
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>Room Status Grid</Typography>
      <Divider sx={{ mb: 2 }} />
      {Object.entries(groups).map(([name, list]) => (
        <Box key={name} sx={{ mb: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>{name}</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {list.map((r) => (
              <Tooltip key={r.id} title={`${r.room_number} · ${r.status}`}>
                <Box sx={{ width: 70, height: 50, bgcolor: ROOM_COLORS[r.status] || '#aaa', borderRadius: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                  <Typography variant="caption" color="white" fontWeight={700}>{r.room_number}</Typography>
                  <Typography variant="caption" color="white" sx={{ fontSize: 9 }}>{r.status}</Typography>
                </Box>
              </Tooltip>
            ))}
          </Box>
        </Box>
      ))}
    </Paper>
  )
}

export default function OperationalDashboard() {
  const [property, setProperty] = useState('')
  const { data = {}, isLoading, isFetching, error, refetch } = useGetOperationalOverviewQuery({ property_id: property || undefined })

  const allProperties = !property
  const tasks = data.staff_tasks || []
  const rooms = data.rooms || []

  return (
    <AppLayout>
      <AnalyticsHeader title="Operational Dashboard" subtitle={data.date ? `Live status for ${data.date}` : ''}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AnalyticsFilters properties={data.properties || []} property={property} onPropertyChange={setProperty} />
          <Tooltip title="Refresh"><IconButton onClick={refetch}><Refresh /></IconButton></Tooltip>
        </Box>
      </AnalyticsHeader>
      {error && <ErrorAlert error={error} />}
      {isLoading || isFetching ? <LoadingSpinner /> : (
        <>
          <StatusTiles status={data.room_status || {}} />
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={6}>
              <GuestMovementList title="Arrivals Today" items={data.checkins_today || []} emptyText="No arrivals today." avatarColor="primary.main" showProperty={allProperties} />
            </Grid>
            <Grid item xs={12} md={6}>
              <GuestMovementList title="Departures Today" items={data.checkouts_today || []} emptyText="No departures today." avatarColor="secondary.main" showProperty={allProperties} />
            </Grid>
          </Grid>
          {tasks.length > 0 && (
            <Paper sx={{ p: 2, mb: 4 }}>
              <Typography variant="h6" gutterBottom>Staff Tasks</Typography>
              <Divider sx={{ mb: 1 }} />
              <DataTable columns={taskColumns(allProperties)} rows={tasks} />
            </Paper>
          )}
          {rooms.length > 0 && <RoomGrid rooms={rooms} />}
        </>
      )}
    </AppLayout>
  )
}
