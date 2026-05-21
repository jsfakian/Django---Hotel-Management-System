import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, Paper, Typography, Grid, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import { ArrowBack, Edit, Delete } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import DataTable from '../../../components/common/DataTable'
import { useGetEventQuery, useDeleteEventMutation } from '../../../features/events/eventsApi'

const attendeeColumns = [
  { field: 'guest_name', headerName: 'Guest', width: 200 },
  { field: 'email', headerName: 'Email', width: 220 },
  { field: 'registered_at', headerName: 'Registered', width: 140, renderCell: (r) => r.registered_at ? new Date(r.registered_at).toLocaleDateString() : '—' },
]

export default function EventDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [deleteOpen, setDeleteOpen] = useState(false)
  const { data: event, isLoading, error } = useGetEventQuery(id)
  const [deleteEvent, { isLoading: deleting }] = useDeleteEventMutation()

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!event) return null

  const handleDelete = async () => {
    await deleteEvent(id)
    navigate('/admin/events')
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/admin/events')}>Back</Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<Edit />} onClick={() => navigate(`/admin/events/${id}/edit`)}>Edit</Button>
          <Button variant="outlined" color="error" startIcon={<Delete />} onClick={() => setDeleteOpen(true)}>Delete</Button>
        </Box>
      </Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>{event.title}</Typography>
        <Grid container spacing={2}>
          {[['Date', event.date], ['Time', event.time], ['Location', event.location], ['Capacity', event.capacity], ['Registered', event.attendees_count || 0], ['Property', event.property_name || event.property]].map(([label, val]) => (
            <Grid item xs={12} sm={6} md={4} key={label}>
              <Typography variant="caption" color="text.secondary">{label}</Typography>
              <Typography>{val || '—'}</Typography>
            </Grid>
          ))}
          {event.description && <Grid item xs={12}><Typography variant="caption" color="text.secondary">Description</Typography><Typography variant="body2">{event.description}</Typography></Grid>}
        </Grid>
      </Paper>
      <Typography variant="h6" sx={{ mb: 1 }}>Attendees</Typography>
      <DataTable columns={attendeeColumns} rows={event.attendees || []} />
      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)}>
        <DialogTitle>Delete "{event.title}"?</DialogTitle>
        <DialogContent>This cannot be undone.</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteOpen(false)}>Cancel</Button>
          <Button color="error" onClick={handleDelete} disabled={deleting}>Delete</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
