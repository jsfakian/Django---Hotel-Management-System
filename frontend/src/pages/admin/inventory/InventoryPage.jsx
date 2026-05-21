import React, { useState } from 'react'
import {
  Box, Paper, Typography, MenuItem, TextField, Grid, Chip, Table, TableBody,
  TableCell, TableHead, TableRow, Button, Dialog, DialogTitle, DialogContent,
  DialogActions, Alert, CircularProgress,
} from '@mui/material'
import { Refresh } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import ErrorAlert from '../../../components/common/ErrorAlert'
import {
  useGetPropertyAvailabilityQuery,
  useUpdateRoomAvailabilityMutation,
  useGetSyncLogQuery,
} from '../../../features/inventory/inventoryApi'
import { useGetPropertiesQuery } from '../../../features/properties/propertiesApi'

const STATUS_COLORS = { available: 'success', occupied: 'error', maintenance: 'warning', blocked: 'default' }

export default function InventoryPage() {
  const [propertyId, setPropertyId] = useState('')
  const [editTarget, setEditTarget] = useState(null)
  const [editStatus, setEditStatus] = useState('')
  const [msg, setMsg] = useState(null)

  const { data: properties } = useGetPropertiesQuery()
  const propertyList = properties?.results || properties || []

  const { data: availability, isLoading, error, refetch } = useGetPropertyAvailabilityQuery(propertyId, { skip: !propertyId })
  const { data: syncLog } = useGetSyncLogQuery(propertyId, { skip: !propertyId })
  const [updateAvailability, { isLoading: updating }] = useUpdateRoomAvailabilityMutation()

  const rooms = availability?.rooms || availability || []

  const handleUpdate = async () => {
    const result = await updateAvailability({ roomId: editTarget.id, status: editStatus })
    if (result.error) {
      setMsg({ type: 'error', text: 'Failed to update availability.' })
    } else {
      setMsg({ type: 'success', text: 'Room availability updated.' })
      setEditTarget(null)
    }
  }

  return (
    <AppLayout>
      <Typography variant="h5" sx={{ mb: 3 }}>Inventory Management</Typography>
      {msg && <Alert severity={msg.type} sx={{ mb: 2 }} onClose={() => setMsg(null)}>{msg.text}</Alert>}

      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            select label="Select Property" value={propertyId} onChange={(e) => setPropertyId(e.target.value)}
            sx={{ minWidth: 240 }} size="small"
          >
            {propertyList.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
          </TextField>
          <Button startIcon={<Refresh />} onClick={refetch} disabled={!propertyId || isLoading}>Refresh</Button>
        </Box>
      </Paper>

      {error && <ErrorAlert error={error} />}

      {isLoading && <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>}

      {!isLoading && rooms.length > 0 && (
        <Paper sx={{ mb: 3 }}>
          <Table>
            <TableHead>
              <TableRow>
                {['Room', 'Type', 'Floor', 'Status', 'Actions'].map((h) => <TableCell key={h}>{h}</TableCell>)}
              </TableRow>
            </TableHead>
            <TableBody>
              {rooms.map((room) => (
                <TableRow key={room.id}>
                  <TableCell>{room.room_number || room.number}</TableCell>
                  <TableCell>{room.room_type_name || room.room_type}</TableCell>
                  <TableCell>{room.floor || '—'}</TableCell>
                  <TableCell>
                    <Chip size="small" label={room.status} color={STATUS_COLORS[room.status] || 'default'} />
                  </TableCell>
                  <TableCell>
                    <Button size="small" onClick={() => { setEditTarget(room); setEditStatus(room.status) }}>
                      Update
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {!isLoading && propertyId && rooms.length === 0 && (
        <Typography color="text.secondary">No rooms found for this property.</Typography>
      )}

      {syncLog && Array.isArray(syncLog) && syncLog.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Sync Log</Typography>
          <Table size="small">
            <TableHead>
              <TableRow>{['Channel', 'Status', 'Timestamp', 'Message'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow>
            </TableHead>
            <TableBody>
              {syncLog.slice(0, 20).map((entry, i) => (
                <TableRow key={i}>
                  <TableCell>{entry.channel_name || entry.channel}</TableCell>
                  <TableCell><Chip size="small" label={entry.status} color={entry.status === 'success' ? 'success' : 'error'} /></TableCell>
                  <TableCell>{entry.created_at ? new Date(entry.created_at).toLocaleString() : '—'}</TableCell>
                  <TableCell>{entry.message || '—'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      <Dialog open={Boolean(editTarget)} onClose={() => setEditTarget(null)}>
        <DialogTitle>Update Room {editTarget?.room_number || editTarget?.number}</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <TextField
            select fullWidth label="Status" value={editStatus}
            onChange={(e) => setEditStatus(e.target.value)}
          >
            {['available', 'occupied', 'maintenance', 'blocked'].map((s) => (
              <MenuItem key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditTarget(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleUpdate} disabled={updating}>Update</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
