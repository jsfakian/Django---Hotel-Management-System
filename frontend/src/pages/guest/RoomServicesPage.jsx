import React, { useState } from 'react'
import { Box, Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions, TextField, FormControl, InputLabel, Select, MenuItem, Grid } from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import DataTable from '../../components/common/DataTable'
import ErrorAlert from '../../components/common/ErrorAlert'
import {
  useGetRoomServicesQuery,
  useGetCurrentRoomServicesQuery,
  useGetActiveRoomServicesQuery,
  useCreateRoomServiceMutation,
} from '../../features/room-services/roomServicesApi'

const STATUS_COLORS = { pending: 'warning', in_progress: 'info', completed: 'success', cancelled: 'error' }
const columns = [
  { field: 'service_type', headerName: 'Type', width: 140 },
  { field: 'description', headerName: 'Description', width: 240 },
  { field: 'status', headerName: 'Status', width: 120, renderCell: (r) => <Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} /> },
  { field: 'requested_at', headerName: 'Requested', width: 160, renderCell: (r) => r.requested_at ? new Date(r.requested_at).toLocaleString() : '—' },
]

export default function RoomServicesPage() {
  const [viewMode, setViewMode] = useState('current')
  const [newOpen, setNewOpen] = useState(false)
  const [form, setForm] = useState({ service_type: 'cleaning', description: '' })
  const allQuery = useGetRoomServicesQuery({}, { skip: viewMode !== 'all' })
  const currentQuery = useGetCurrentRoomServicesQuery({}, { skip: viewMode !== 'current' })
  const activeQuery = useGetActiveRoomServicesQuery({}, { skip: viewMode !== 'active' })
  const selectedQuery = viewMode === 'current' ? currentQuery : viewMode === 'active' ? activeQuery : allQuery
  const { data, isLoading, error } = selectedQuery
  const [createRoomService, { isLoading: creating }] = useCreateRoomServiceMutation()
  const rows = data?.results || data || []

  const handleCreate = async (e) => {
    e.preventDefault()
    const result = await createRoomService(form)
    if (!result.error) { setNewOpen(false); setForm({ service_type: 'cleaning', description: '' }) }
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>View</InputLabel>
          <Select value={viewMode} label="View" onChange={(e) => setViewMode(e.target.value)}>
            <MenuItem value="current">Current</MenuItem>
            <MenuItem value="active">Active</MenuItem>
            <MenuItem value="all">All</MenuItem>
          </Select>
        </FormControl>
        <Button variant="contained" startIcon={<Add />} onClick={() => setNewOpen(true)}>Request Service</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} />
      <Dialog open={newOpen} onClose={() => setNewOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Request Room Service</DialogTitle>
        <Box component="form" onSubmit={handleCreate}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControl fullWidth><InputLabel>Service Type</InputLabel>
                  <Select value={form.service_type} label="Service Type" onChange={(e) => setForm((f) => ({ ...f, service_type: e.target.value }))}>
                    {['cleaning', 'maintenance', 'food', 'laundry', 'other'].map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}><TextField fullWidth multiline rows={3} required label="Description" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} /></Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setNewOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={creating}>Submit</Button>
          </DialogActions>
        </Box>
      </Dialog>
    </AppLayout>
  )
}
