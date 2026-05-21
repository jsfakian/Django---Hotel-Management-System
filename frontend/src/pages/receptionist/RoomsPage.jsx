import React, { useState } from 'react'
import { Box, TextField, Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Grid, Chip } from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import DataTable from '../../components/common/DataTable'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetRoomsQuery } from '../../features/rooms/roomsApi'

const STATUS_COLORS = { available: 'success', occupied: 'primary', maintenance: 'error', cleaning: 'warning', blocked: 'default' }

const columns = [
  { field: 'room_number', headerName: 'Room #', width: 100 },
  { field: 'room_type', headerName: 'Type', width: 120 },
  { field: 'capacity', headerName: 'Capacity', width: 100 },
  { field: 'beds', headerName: 'Beds', width: 80 },
  { field: 'price_per_night', headerName: 'Price/Night (€)', width: 140, renderCell: (r) => `€${Number(r.price_per_night || 0).toFixed(2)}` },
  { field: 'status', headerName: 'Status', width: 120 },
]

export default function RoomsPage() {
  const [checkIn, setCheckIn] = useState('')
  const [checkOut, setCheckOut] = useState('')
  const [selected, setSelected] = useState(null)
  const { data, isLoading, error } = useGetRoomsQuery({ check_in: checkIn || undefined, check_out: checkOut || undefined })
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <TextField size="small" label="Check-in" type="date" InputLabelProps={{ shrink: true }} value={checkIn} onChange={(e) => setCheckIn(e.target.value)} />
        <TextField size="small" label="Check-out" type="date" InputLabelProps={{ shrink: true }} value={checkOut} onChange={(e) => setCheckOut(e.target.value)} />
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={setSelected} />
      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} maxWidth="sm" fullWidth>
        {selected && (
          <>
            <DialogTitle>Room {selected.room_number}</DialogTitle>
            <DialogContent>
              <Grid container spacing={2} sx={{ mt: 0 }}>
                <Grid item xs={6}><Typography variant="caption" color="text.secondary">Type</Typography><Typography>{selected.room_type}</Typography></Grid>
                <Grid item xs={6}><Typography variant="caption" color="text.secondary">Status</Typography><br /><Chip size="small" label={selected.status} color={STATUS_COLORS[selected.status] || 'default'} /></Grid>
                <Grid item xs={6}><Typography variant="caption" color="text.secondary">Capacity</Typography><Typography>{selected.capacity}</Typography></Grid>
                <Grid item xs={6}><Typography variant="caption" color="text.secondary">Beds</Typography><Typography>{selected.beds}</Typography></Grid>
                <Grid item xs={6}><Typography variant="caption" color="text.secondary">Price/Night</Typography><Typography>€{Number(selected.price_per_night || 0).toFixed(2)}</Typography></Grid>
                <Grid item xs={6}><Typography variant="caption" color="text.secondary">Property</Typography><Typography>{selected.property_name || selected.property}</Typography></Grid>
              </Grid>
            </DialogContent>
            <DialogActions><Button onClick={() => setSelected(null)}>Close</Button></DialogActions>
          </>
        )}
      </Dialog>
    </AppLayout>
  )
}
