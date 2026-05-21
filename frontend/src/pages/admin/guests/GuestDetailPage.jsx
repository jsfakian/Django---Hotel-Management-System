import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, Paper, Typography, Grid, Dialog, DialogTitle, DialogContent, DialogActions, Chip } from '@mui/material'
import { ArrowBack, Edit, Delete } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import DataTable from '../../../components/common/DataTable'
import { useGetGuestQuery, useDeleteGuestMutation } from '../../../features/guests/guestsApi'
import { useGetBookingsQuery } from '../../../features/bookings/bookingsApi'

const bookingColumns = [
  { field: 'id', headerName: 'ID', width: 60 },
  { field: 'room_number', headerName: 'Room', width: 100 },
  { field: 'check_in_date', headerName: 'Check-in', width: 120 },
  { field: 'check_out_date', headerName: 'Check-out', width: 120 },
  { field: 'status', headerName: 'Status', width: 120, renderCell: (row) => <Chip size="small" label={row.status} /> },
  { field: 'total_price', headerName: 'Total', width: 100, renderCell: (row) => `€${Number(row.total_price || 0).toFixed(2)}` },
]

export default function GuestDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [deleteOpen, setDeleteOpen] = useState(false)
  const { data: guest, isLoading, error } = useGetGuestQuery(id)
  const { data: bookingsData } = useGetBookingsQuery({ guest: id })
  const [deleteGuest, { isLoading: deleting }] = useDeleteGuestMutation()
  const bookings = bookingsData?.results || bookingsData || []

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!guest) return null

  const handleDelete = async () => {
    await deleteGuest(id)
    navigate('/admin/guests')
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/admin/guests')}>Back</Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<Edit />} onClick={() => navigate(`/admin/guests/${id}/edit`)}>Edit</Button>
          <Button variant="outlined" color="error" startIcon={<Delete />} onClick={() => setDeleteOpen(true)}>Delete</Button>
        </Box>
      </Box>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>{guest.first_name} {guest.last_name}</Typography>
        <Grid container spacing={2}>
          {[['Email', guest.email], ['Phone', guest.phone], ['Address', guest.address], ['City', guest.city], ['Country', guest.country], ['Nationality', guest.nationality], ['Date of Birth', guest.date_of_birth], ['Passport/ID', guest.passport_number]].map(([label, val]) => (
            <Grid item xs={12} sm={6} md={4} key={label}>
              <Typography variant="caption" color="text.secondary">{label}</Typography>
              <Typography variant="body1">{val || '—'}</Typography>
            </Grid>
          ))}
        </Grid>
      </Paper>
      <Typography variant="h6" sx={{ mb: 1 }}>Recent Bookings</Typography>
      <DataTable columns={bookingColumns} rows={bookings} onRowClick={(row) => navigate(`/admin/bookings/${row.id}`)} />
      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)}>
        <DialogTitle>Delete guest {guest.first_name} {guest.last_name}?</DialogTitle>
        <DialogContent>This action cannot be undone.</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteOpen(false)}>Cancel</Button>
          <Button color="error" onClick={handleDelete} disabled={deleting}>Delete</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
