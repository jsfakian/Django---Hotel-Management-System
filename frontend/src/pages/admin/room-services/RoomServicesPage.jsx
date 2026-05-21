import React, { useState } from 'react'
import { Box, Button, Chip, FormControl, InputLabel, Select, MenuItem, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Grid } from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import {
  useGetRoomServicesQuery,
  useGetCurrentRoomServicesQuery,
  useGetActiveRoomServicesQuery,
  useCreateRoomServiceMutation,
  useUpdateRoomServiceMutation,
} from '../../../features/room-services/roomServicesApi'

const STATUS_COLORS = { pending: 'warning', in_progress: 'info', completed: 'success', cancelled: 'error' }

export default function RoomServicesPage() {
  const [status, setStatus] = useState('')
  const [viewMode, setViewMode] = useState('all')
  const [newOpen, setNewOpen] = useState(false)
  const [form, setForm] = useState({ room: '', service_type: 'cleaning', description: '' })
  const allQuery = useGetRoomServicesQuery({ status: status || undefined }, { skip: viewMode !== 'all' })
  const currentQuery = useGetCurrentRoomServicesQuery({}, { skip: viewMode !== 'current' })
  const activeQuery = useGetActiveRoomServicesQuery({}, { skip: viewMode !== 'active' })
  const [createRoomService, { isLoading: creating }] = useCreateRoomServiceMutation()
  const [updateRoomService] = useUpdateRoomServiceMutation()
  const selectedQuery = viewMode === 'current' ? currentQuery : viewMode === 'active' ? activeQuery : allQuery
  const { data, isLoading, error } = selectedQuery
  const rows = data?.results || data || []

  const handleCreate = async (e) => {
    e.preventDefault()
    const result = await createRoomService(form)
    if (!result.error) { setNewOpen(false); setForm({ room: '', service_type: 'cleaning', description: '' }) }
  }

  const columns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'room_number', headerName: 'Room', width: 100 },
    { field: 'guest_name', headerName: 'Guest', width: 160 },
    { field: 'service_type', headerName: 'Type', width: 130 },
    { field: 'description', headerName: 'Description', width: 200 },
    { field: 'status', headerName: 'Status', width: 120, renderCell: (r) => <Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} /> },
    { field: 'requested_at', headerName: 'Requested', width: 130, renderCell: (r) => r.requested_at ? new Date(r.requested_at).toLocaleString() : '—' },
    { field: 'actions', headerName: '', width: 180, renderCell: (r) => (
      <Box>
        {r.status === 'pending' && <Button size="small" onClick={(e) => { e.stopPropagation(); updateRoomService({ id: r.id, status: 'in_progress' }) }}>Start</Button>}
        {r.status === 'in_progress' && <Button size="small" onClick={(e) => { e.stopPropagation(); updateRoomService({ id: r.id, status: 'completed' }) }}>Complete</Button>}
      </Box>
    )},
  ]

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>View</InputLabel>
            <Select value={viewMode} label="View" onChange={(e) => setViewMode(e.target.value)}>
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="current">Current</MenuItem>
              <MenuItem value="active">Active</MenuItem>
            </Select>
          </FormControl>
          {viewMode === 'all' && (
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>Status</InputLabel>
              <Select value={status} label="Status" onChange={(e) => setStatus(e.target.value)}>
                {['', 'pending', 'in_progress', 'completed', 'cancelled'].map((s) => <MenuItem key={s} value={s}>{s || 'All'}</MenuItem>)}
              </Select>
            </FormControl>
          )}
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => setNewOpen(true)}>New Request</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} />
      <Dialog open={newOpen} onClose={() => setNewOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Room Service Request</DialogTitle>
        <Box component="form" onSubmit={handleCreate}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12}><TextField fullWidth required label="Room ID or Number" value={form.room} onChange={(e) => setForm((f) => ({ ...f, room: e.target.value }))} /></Grid>
              <Grid item xs={12}>
                <FormControl fullWidth><InputLabel>Service Type</InputLabel>
                  <Select value={form.service_type} label="Service Type" onChange={(e) => setForm((f) => ({ ...f, service_type: e.target.value }))}>
                    {['cleaning', 'maintenance', 'food', 'laundry', 'other'].map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}><TextField fullWidth multiline rows={3} label="Description" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} /></Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setNewOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={creating}>Create</Button>
          </DialogActions>
        </Box>
      </Dialog>
    </AppLayout>
  )
}
