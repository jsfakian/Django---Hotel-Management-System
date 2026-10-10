import React, { useState } from 'react'
import {
  Box, Button, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Grid, Chip, FormControlLabel, Switch,
} from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import {
  useGetRoomTypesQuery,
  useCreateRoomTypeMutation,
  useUpdateRoomTypeMutation,
  useDeleteRoomTypeMutation,
} from '../../../features/catalog/catalogApi'

const EMPTY = {
  property: '',
  code: '',
  name: '',
  capacity: 2,
  max_occupancy: 2,
  base_occupancy: 2,
  base_price: '',
  is_active: true,
}

function RoomTypeForm({ form, setForm }) {
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={4}>
        <TextField fullWidth required label="Property ID" type="number" value={form.property} onChange={set('property')} />
      </Grid>
      <Grid item xs={12} sm={4}>
        <TextField fullWidth required label="Code" value={form.code} onChange={set('code')} />
      </Grid>
      <Grid item xs={12} sm={4}>
        <TextField fullWidth required label="Name" value={form.name} onChange={set('name')} />
      </Grid>
      <Grid item xs={6} sm={3}>
        <TextField fullWidth label="Capacity" type="number" value={form.capacity} onChange={set('capacity')} />
      </Grid>
      <Grid item xs={6} sm={3}>
        <TextField fullWidth label="Max occupancy" type="number" value={form.max_occupancy} onChange={set('max_occupancy')} />
      </Grid>
      <Grid item xs={6} sm={3}>
        <TextField fullWidth label="Base occupancy" type="number" value={form.base_occupancy} onChange={set('base_occupancy')} />
      </Grid>
      <Grid item xs={6} sm={3}>
        <TextField fullWidth label="Base price (€)" type="number" value={form.base_price} onChange={set('base_price')} />
      </Grid>
      <Grid item xs={12}>
        <FormControlLabel
          control={<Switch checked={Boolean(form.is_active)} onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))} />}
          label="Active"
        />
      </Grid>
    </Grid>
  )
}

function toPayload(form) {
  return {
    property: Number(form.property),
    code: form.code,
    name: form.name,
    capacity: Number(form.capacity) || 1,
    max_occupancy: Number(form.max_occupancy) || 1,
    base_occupancy: Number(form.base_occupancy) || 1,
    base_price: form.base_price === '' ? null : Number(form.base_price),
    is_active: Boolean(form.is_active),
  }
}

export default function RoomTypesPage() {
  const [open, setOpen] = useState(false)
  const [editTarget, setEditTarget] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [form, setForm] = useState(EMPTY)

  const { data, isLoading, error } = useGetRoomTypesQuery()
  const [createRoomType, { isLoading: creating }] = useCreateRoomTypeMutation()
  const [updateRoomType, { isLoading: updating }] = useUpdateRoomTypeMutation()
  const [deleteRoomType, { isLoading: deleting }] = useDeleteRoomTypeMutation()
  const rows = data?.results || data || []

  const columns = [
    { field: 'code', headerName: 'Code', width: 100 },
    { field: 'name', headerName: 'Name', width: 180 },
    { field: 'property', headerName: 'Property', width: 100 },
    { field: 'capacity', headerName: 'Capacity', width: 90 },
    { field: 'max_occupancy', headerName: 'Max occ.', width: 90 },
    { field: 'base_price', headerName: 'Base €', width: 100, renderCell: (r) => (r.base_price != null ? `€${Number(r.base_price).toFixed(2)}` : '—') },
    { field: 'is_active', headerName: 'Status', width: 90, renderCell: (r) => <Chip size="small" label={r.is_active ? 'Active' : 'Off'} color={r.is_active ? 'success' : 'default'} /> },
    {
      field: 'actions',
      headerName: '',
      width: 160,
      renderCell: (r) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button size="small" onClick={(e) => { e.stopPropagation(); setForm({ ...EMPTY, ...r, base_price: r.base_price ?? '' }); setEditTarget(r) }}>Edit</Button>
          <Button size="small" color="error" onClick={(e) => { e.stopPropagation(); setDeleteTarget(r) }}>Delete</Button>
        </Box>
      ),
    },
  ]

  const handleCreate = async (e) => {
    e.preventDefault()
    const result = await createRoomType(toPayload(form))
    if (!result.error) { setOpen(false); setForm(EMPTY) }
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    const result = await updateRoomType({ id: editTarget.id, ...toPayload(form) })
    if (!result.error) setEditTarget(null)
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" startIcon={<Add />} onClick={() => { setForm(EMPTY); setOpen(true) }}>Add Room Type</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} />

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Room Type</DialogTitle>
        <Box component="form" onSubmit={handleCreate}>
          <DialogContent><RoomTypeForm form={form} setForm={setForm} /></DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={creating}>Add</Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog open={Boolean(editTarget)} onClose={() => setEditTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Room Type</DialogTitle>
        <Box component="form" onSubmit={handleUpdate}>
          <DialogContent><RoomTypeForm form={form} setForm={setForm} /></DialogContent>
          <DialogActions>
            <Button onClick={() => setEditTarget(null)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={updating}>Save</Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Delete &quot;{deleteTarget?.name}&quot;?</DialogTitle>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button color="error" disabled={deleting} onClick={async () => { await deleteRoomType(deleteTarget.id); setDeleteTarget(null) }}>Delete</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
