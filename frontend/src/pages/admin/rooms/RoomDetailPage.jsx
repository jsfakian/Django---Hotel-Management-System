import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, Paper, Typography, Grid, Chip, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import { Edit, Delete, ArrowBack } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetRoomQuery, useDeleteRoomMutation } from '../../../features/rooms/roomsApi'

const STATUS_COLORS = { available: 'success', occupied: 'primary', maintenance: 'error', cleaning: 'warning', blocked: 'default' }

export default function RoomDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [deleteOpen, setDeleteOpen] = useState(false)
  const { data: room, isLoading, error } = useGetRoomQuery(id)
  const [deleteRoom, { isLoading: deleting }] = useDeleteRoomMutation()

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!room) return null

  const handleDelete = async () => {
    await deleteRoom(id)
    navigate('/admin/rooms')
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/admin/rooms')}>Back</Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<Edit />} onClick={() => navigate(`/admin/rooms/${id}/edit`)}>Edit</Button>
          <Button variant="outlined" color="error" startIcon={<Delete />} onClick={() => setDeleteOpen(true)}>Delete</Button>
        </Box>
      </Box>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Typography variant="h5">Room {room.room_number}</Typography>
          <Chip label={room.status} color={STATUS_COLORS[room.status] || 'default'} />
        </Box>
        <Grid container spacing={2}>
          {[
            ['Type', room.room_type],
            ['Capacity', room.capacity],
            ['Beds', room.beds],
            ['Price / Night', `€${Number(room.price_per_night || 0).toFixed(2)}`],
            ['Property', room.property_name || room.property],
            ['Floor', room.floor || '—'],
          ].map(([label, val]) => (
            <Grid item xs={12} sm={6} md={4} key={label}>
              <Typography variant="caption" color="text.secondary">{label}</Typography>
              <Typography variant="body1">{val}</Typography>
            </Grid>
          ))}
        </Grid>
        {room.description && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary">Description</Typography>
            <Typography variant="body2">{room.description}</Typography>
          </Box>
        )}
      </Paper>
      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)}>
        <DialogTitle>Delete Room {room.room_number}?</DialogTitle>
        <DialogContent>This action cannot be undone.</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteOpen(false)}>Cancel</Button>
          <Button color="error" onClick={handleDelete} disabled={deleting}>Delete</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
