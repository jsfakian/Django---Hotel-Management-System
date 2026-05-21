import React, { useState } from 'react'
import { Box, Grid, Card, CardContent, Typography, IconButton, Paper, List, ListItem, ListItemAvatar, ListItemText, Avatar, Chip, Divider } from '@mui/material'
import { Refresh, Hotel, CleaningServices, Build, Block } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import DataTable from '../../components/common/DataTable'
import { useGetOperationalDashboardQuery } from '../../features/analytics/analyticsApi'

const ROOM_COLORS = { occupied: '#1565C0', available: '#2E7D32', cleaning: '#E65100', maintenance: '#B71C1C', blocked: '#424242' }
const PRIORITY_COLORS = { high: 'error', medium: 'warning', low: 'success' }

const taskColumns = [
  { field: 'title', headerName: 'Task', width: 200 },
  { field: 'employee_name', headerName: 'Employee', width: 160 },
  { field: 'priority', headerName: 'Priority', width: 110, renderCell: (r) => <Chip size="small" label={r.priority} color={PRIORITY_COLORS[r.priority] || 'default'} /> },
  { field: 'status', headerName: 'Status', width: 110 },
  { field: 'due_time', headerName: 'Due', width: 120 },
]

export default function OperationalDashboard() {
  const [, forceRefresh] = useState(0)
  const { data, isLoading, error, refetch } = useGetOperationalDashboardQuery()

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>

  const status = data?.room_status || {}
  const checkIns = data?.checkins_today || []
  const checkOuts = data?.checkouts_today || []
  const tasks = data?.staff_tasks || []
  const rooms = data?.rooms || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Operational Dashboard</Typography>
        <IconButton onClick={() => { refetch(); forceRefresh(n => n + 1) }}><Refresh /></IconButton>
      </Box>
      {error && <ErrorAlert error={error} />}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {[['Occupied', status.occupied, 'primary'], ['Available', status.available, 'success'], ['Cleaning', status.cleaning, 'warning'], ['Maintenance', status.maintenance, 'error'], ['Blocked', status.blocked, 'default'], ['Total', status.total, 'info']].map(([label, count, color]) => (
          <Grid item xs={6} sm={4} md={2} key={label}>
            <Card><CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h4" fontWeight={700} color={`${color}.main`}>{count || 0}</Typography>
              <Typography variant="body2" color="text.secondary">{label}</Typography>
            </CardContent></Card>
          </Grid>
        ))}
      </Grid>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Check-ins Today ({checkIns.length})</Typography>
            <Divider sx={{ mb: 1 }} />
            <List dense>{checkIns.length ? checkIns.map((c, i) => (
              <ListItem key={i}><ListItemAvatar><Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32, fontSize: 14 }}>{(c.guest_name || 'G')[0]}</Avatar></ListItemAvatar><ListItemText primary={c.guest_name} secondary={`Room ${c.room_number} · Booking #${c.booking_id}`} /></ListItem>
            )) : <Typography color="text.secondary" variant="body2">No check-ins today.</Typography>}</List>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>Check-outs Today ({checkOuts.length})</Typography>
            <Divider sx={{ mb: 1 }} />
            <List dense>{checkOuts.length ? checkOuts.map((c, i) => (
              <ListItem key={i}><ListItemAvatar><Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32, fontSize: 14 }}>{(c.guest_name || 'G')[0]}</Avatar></ListItemAvatar><ListItemText primary={c.guest_name} secondary={`Room ${c.room_number} · Booking #${c.booking_id}`} /></ListItem>
            )) : <Typography color="text.secondary" variant="body2">No check-outs today.</Typography>}</List>
          </Paper>
        </Grid>
      </Grid>
      {tasks.length > 0 && (
        <Paper sx={{ p: 2, mb: 4 }}>
          <Typography variant="h6" gutterBottom>Staff Tasks</Typography>
          <Divider sx={{ mb: 1 }} />
          <DataTable columns={taskColumns} rows={tasks} />
        </Paper>
      )}
      {rooms.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Room Status Grid</Typography>
          <Divider sx={{ mb: 2 }} />
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {rooms.map((r) => (
              <Box key={r.id} sx={{ width: 70, height: 50, bgcolor: ROOM_COLORS[r.status] || '#aaa', borderRadius: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', cursor: 'default' }}>
                <Typography variant="caption" color="white" fontWeight={700}>{r.room_number}</Typography>
                <Typography variant="caption" color="white" sx={{ fontSize: 9 }}>{r.status}</Typography>
              </Box>
            ))}
          </Box>
        </Paper>
      )}
    </AppLayout>
  )
}
