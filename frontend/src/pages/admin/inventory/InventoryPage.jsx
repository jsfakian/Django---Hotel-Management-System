import React, { useState } from 'react'
import {
  Box, Paper, Typography, MenuItem, TextField, Chip, Table, TableBody,
  TableCell, TableHead, TableRow, Button, Dialog, DialogTitle, DialogContent,
  DialogActions, Alert, CircularProgress,
} from '@mui/material'
import { Refresh } from '@mui/icons-material'
import PageShell from '../../../components/common/PageShell'
import ErrorAlert from '../../../components/common/ErrorAlert'
import {
  useGetPropertyAvailabilityQuery,
  useUpdateRoomAvailabilityMutation,
  useGetSyncLogQuery,
} from '../../../features/inventory/inventoryApi'
import { useGetPropertiesQuery } from '../../../features/properties/propertiesApi'

const STATUS_COLORS = { available: 'success', occupied: 'error', maintenance: 'warning', blocked: 'default' }

const listOf = (d) => d?.results || d || []
const DASH = '—'

function RoomsTable({ rooms, onEdit }) {
  return (
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
              <TableCell>{room.floor || DASH}</TableCell>
              <TableCell>
                <Chip size="small" label={room.status} color={STATUS_COLORS[room.status] || 'default'} />
              </TableCell>
              <TableCell>
                <Button size="small" onClick={() => onEdit(room)}>Update</Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  )
}

function SyncLogTable({ entries }) {
  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>Sync Log</Typography>
      <Table size="small">
        <TableHead>
          <TableRow>{['Channel', 'Status', 'Timestamp', 'Message'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow>
        </TableHead>
        <TableBody>
          {entries.slice(0, 20).map((entry, i) => (
            <TableRow key={i}>
              <TableCell>{entry.channel_name || entry.channel}</TableCell>
              <TableCell><Chip size="small" label={entry.status} color={entry.status === 'success' ? 'success' : 'error'} /></TableCell>
              <TableCell>{entry.created_at ? new Date(entry.created_at).toLocaleString() : DASH}</TableCell>
              <TableCell>{entry.message || DASH}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  )
}

function EditStatusDialog({ target, status, onStatusChange, onClose, onSubmit, updating }) {
  return (
    <Dialog open={Boolean(target)} onClose={onClose}>
      <DialogTitle>Update Room {target?.room_number || target?.number}</DialogTitle>
      <DialogContent sx={{ pt: 2 }}>
        <TextField select fullWidth label="Status" value={status} onChange={(e) => onStatusChange(e.target.value)}>
          {['available', 'occupied', 'maintenance', 'blocked'].map((s) => (
            <MenuItem key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</MenuItem>
          ))}
        </TextField>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant="contained" onClick={onSubmit} disabled={updating}>Update</Button>
      </DialogActions>
    </Dialog>
  )
}

function PropertyPicker({ propertyList, propertyId, onChange, onRefresh, disabled }) {
  return (
    <Paper sx={{ p: 2, mb: 3 }}>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
        <TextField
          select label="Select Property" value={propertyId} onChange={(e) => onChange(e.target.value)}
          sx={{ minWidth: 240 }} size="small"
        >
          {propertyList.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
        </TextField>
        <Button startIcon={<Refresh />} onClick={onRefresh} disabled={disabled}>Refresh</Button>
      </Box>
    </Paper>
  )
}

function InventoryBody({
  embedded, msg, setMsg, properties, propertyId, setPropertyId, refetch, isLoading,
  error, rooms, handleEdit, syncLog, editTarget, editStatus, setEditStatus, setEditTarget,
  handleUpdate, updating,
}) {
  return (
    <PageShell embedded={embedded}>
      {!embedded && <Typography variant="h5" sx={{ mb: 3 }}>Inventory Management</Typography>}
      {msg && <Alert severity={msg.type} sx={{ mb: 2 }} onClose={() => setMsg(null)}>{msg.text}</Alert>}

      <PropertyPicker propertyList={listOf(properties)} propertyId={propertyId} onChange={setPropertyId}
        onRefresh={refetch} disabled={!propertyId || isLoading} />

      {error && <ErrorAlert error={error} />}

      {isLoading && <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>}

      {!isLoading && rooms.length > 0 && <RoomsTable rooms={rooms} onEdit={handleEdit} />}

      {!isLoading && propertyId && rooms.length === 0 && (
        <Typography color="text.secondary">No rooms found for this property.</Typography>
      )}

      {Array.isArray(syncLog) && syncLog.length > 0 && <SyncLogTable entries={syncLog} />}

      <EditStatusDialog target={editTarget} status={editStatus} onStatusChange={setEditStatus}
        onClose={() => setEditTarget(null)} onSubmit={handleUpdate} updating={updating} />
    </PageShell>
  )
}

export default function InventoryPage({ embedded = false }) {
  const [propertyId, setPropertyId] = useState('')
  const [editTarget, setEditTarget] = useState(null)
  const [editStatus, setEditStatus] = useState('')
  const [msg, setMsg] = useState(null)

  const { data: properties } = useGetPropertiesQuery()
  const { data: availability, isLoading, error, refetch } = useGetPropertyAvailabilityQuery(propertyId, { skip: !propertyId })
  const { data: syncLog } = useGetSyncLogQuery(propertyId, { skip: !propertyId })
  const [updateAvailability, { isLoading: updating }] = useUpdateRoomAvailabilityMutation()

  const rooms = availability?.rooms || availability || []

  const handleUpdate = async () => {
    const result = await updateAvailability({ roomId: editTarget.id, status: editStatus })
    if (result.error) {
      setMsg({ type: 'error', text: 'Failed to update availability.' })
      return
    }
    setMsg({ type: 'success', text: 'Room availability updated.' })
    setEditTarget(null)
  }

  return (
    <InventoryBody
      embedded={embedded}
      msg={msg}
      setMsg={setMsg}
      properties={properties}
      propertyId={propertyId}
      setPropertyId={setPropertyId}
      refetch={refetch}
      isLoading={isLoading}
      error={error}
      rooms={rooms}
      handleEdit={(room) => { setEditTarget(room); setEditStatus(room.status) }}
      syncLog={syncLog}
      editTarget={editTarget}
      editStatus={editStatus}
      setEditStatus={setEditStatus}
      setEditTarget={setEditTarget}
      handleUpdate={handleUpdate}
      updating={updating}
    />
  )
}
