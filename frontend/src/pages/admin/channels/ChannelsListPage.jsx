import React, { useState } from 'react'
import {
  Box, Button, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Grid, MenuItem, Chip,
} from '@mui/material'
import { Add, Sync } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import {
  useGetChannelsQuery,
  useCreateChannelMutation,
  useDeleteChannelMutation,
  useSyncChannelAvailabilityMutation,
} from '../../../features/channels/channelsApi'

const CHANNEL_CHOICES = ['booking_com', 'airbnb', 'expedia', 'hotels_com', 'agoda', 'direct']

export default function ChannelsListPage() {
  const [newOpen, setNewOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [form, setForm] = useState({ channel_name: '', api_key: '', property: '', is_active: true })

  const { data, isLoading, error } = useGetChannelsQuery()
  const [createChannel, { isLoading: creating }] = useCreateChannelMutation()
  const [deleteChannel, { isLoading: deleting }] = useDeleteChannelMutation()
  const [syncAvailability] = useSyncChannelAvailabilityMutation()

  const rows = data?.results || data || []

  const columns = [
    { field: 'channel_name', headerName: 'Channel', width: 160, renderCell: (r) => r.channel_name?.replace('_', '.') },
    { field: 'property_name', headerName: 'Property', width: 180, renderCell: (r) => r.property_name || r.property },
    { field: 'is_active', headerName: 'Status', width: 100, renderCell: (r) => <Chip size="small" label={r.is_active ? 'Active' : 'Inactive'} color={r.is_active ? 'success' : 'default'} /> },
    { field: 'last_sync_at', headerName: 'Last Sync', width: 160, renderCell: (r) => r.last_sync_at ? new Date(r.last_sync_at).toLocaleString() : '—' },
    {
      field: 'actions', headerName: '', width: 180, renderCell: (r) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button size="small" startIcon={<Sync />} onClick={(e) => { e.stopPropagation(); syncAvailability(r.id) }}>Sync</Button>
          <Button size="small" color="error" onClick={(e) => { e.stopPropagation(); setDeleteTarget(r) }}>Delete</Button>
        </Box>
      ),
    },
  ]

  const handleCreate = async (e) => {
    e.preventDefault()
    const result = await createChannel(form)
    if (!result.error) { setNewOpen(false); setForm({ channel_name: '', api_key: '', property: '', is_active: true }) }
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" startIcon={<Add />} onClick={() => setNewOpen(true)}>Add Channel</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} />

      <Dialog open={newOpen} onClose={() => setNewOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add OTA Channel</DialogTitle>
        <Box component="form" onSubmit={handleCreate}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  select fullWidth required label="Channel"
                  value={form.channel_name}
                  onChange={(e) => setForm((f) => ({ ...f, channel_name: e.target.value }))}
                >
                  {CHANNEL_CHOICES.map((c) => <MenuItem key={c} value={c}>{c.replace('_', '.')}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField fullWidth required label="Property ID" type="number" value={form.property} onChange={(e) => setForm((f) => ({ ...f, property: e.target.value }))} />
              </Grid>
              <Grid item xs={12}>
                <TextField fullWidth required label="API Key" value={form.api_key} onChange={(e) => setForm((f) => ({ ...f, api_key: e.target.value }))} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField select fullWidth label="Status" value={form.is_active} onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.value }))}>
                  <MenuItem value={true}>Active</MenuItem>
                  <MenuItem value={false}>Inactive</MenuItem>
                </TextField>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setNewOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={creating}>Add</Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Remove "{deleteTarget?.channel_name}" channel?</DialogTitle>
        <DialogContent>This will stop syncing bookings from this channel.</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button color="error" onClick={async () => { await deleteChannel(deleteTarget.id); setDeleteTarget(null) }} disabled={deleting}>Remove</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
