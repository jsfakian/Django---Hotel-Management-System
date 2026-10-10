import React, { useState } from 'react'
import {
  Box, Button, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Grid, Chip, FormControlLabel, Switch, MenuItem,
} from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import {
  useGetRatePlansQuery,
  useCreateRatePlanMutation,
  useUpdateRatePlanMutation,
  useDeleteRatePlanMutation,
  useGetRoomTypesQuery,
} from '../../../features/catalog/catalogApi'

const MEAL_PLANS = [
  { value: 'RO', label: 'Room only' },
  { value: 'BB', label: 'Bed & breakfast' },
  { value: 'HB', label: 'Half board' },
  { value: 'FB', label: 'Full board' },
  { value: 'AI', label: 'All inclusive' },
]

const EMPTY = {
  property: '',
  code: '',
  name: '',
  meal_plan: 'RO',
  is_refundable: true,
  cancellation_policy: '',
  room_types: [],
  is_active: true,
}

function RatePlanForm({ form, setForm, roomTypes }) {
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
      <Grid item xs={12} sm={6}>
        <TextField select fullWidth label="Meal plan" value={form.meal_plan} onChange={set('meal_plan')}>
          {MEAL_PLANS.map((m) => <MenuItem key={m.value} value={m.value}>{m.label}</MenuItem>)}
        </TextField>
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField
          select
          fullWidth
          SelectProps={{ multiple: true }}
          label="Room types"
          value={form.room_types}
          onChange={(e) => setForm((f) => ({ ...f, room_types: e.target.value }))}
        >
          {roomTypes.map((rt) => (
            <MenuItem key={rt.id} value={rt.id}>{rt.code} — {rt.name}</MenuItem>
          ))}
        </TextField>
      </Grid>
      <Grid item xs={12}>
        <TextField fullWidth multiline minRows={2} label="Cancellation policy" value={form.cancellation_policy} onChange={set('cancellation_policy')} />
      </Grid>
      <Grid item xs={12} sx={{ display: 'flex', gap: 2 }}>
        <FormControlLabel
          control={<Switch checked={Boolean(form.is_refundable)} onChange={(e) => setForm((f) => ({ ...f, is_refundable: e.target.checked }))} />}
          label="Refundable"
        />
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
    meal_plan: form.meal_plan,
    is_refundable: Boolean(form.is_refundable),
    cancellation_policy: form.cancellation_policy,
    room_types: form.room_types,
    is_active: Boolean(form.is_active),
  }
}

export default function RatePlansPage() {
  const [open, setOpen] = useState(false)
  const [editTarget, setEditTarget] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [form, setForm] = useState(EMPTY)

  const { data, isLoading, error } = useGetRatePlansQuery()
  const { data: roomTypeData } = useGetRoomTypesQuery()
  const [createRatePlan, { isLoading: creating }] = useCreateRatePlanMutation()
  const [updateRatePlan, { isLoading: updating }] = useUpdateRatePlanMutation()
  const [deleteRatePlan, { isLoading: deleting }] = useDeleteRatePlanMutation()

  const rows = data?.results || data || []
  const roomTypes = roomTypeData?.results || roomTypeData || []

  const columns = [
    { field: 'code', headerName: 'Code', width: 100 },
    { field: 'name', headerName: 'Name', width: 180 },
    { field: 'meal_plan', headerName: 'Meal', width: 80 },
    { field: 'is_refundable', headerName: 'Refundable', width: 110, renderCell: (r) => (r.is_refundable ? 'Yes' : 'No') },
    { field: 'property', headerName: 'Property', width: 100 },
    { field: 'is_active', headerName: 'Status', width: 90, renderCell: (r) => <Chip size="small" label={r.is_active ? 'Active' : 'Off'} color={r.is_active ? 'success' : 'default'} /> },
    {
      field: 'actions',
      headerName: '',
      width: 160,
      renderCell: (r) => (
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            size="small"
            onClick={(e) => {
              e.stopPropagation()
              setForm({
                ...EMPTY,
                ...r,
                room_types: (r.room_types || []).map((x) => (typeof x === 'object' ? x.id : x)),
              })
              setEditTarget(r)
            }}
          >
            Edit
          </Button>
          <Button size="small" color="error" onClick={(e) => { e.stopPropagation(); setDeleteTarget(r) }}>Delete</Button>
        </Box>
      ),
    },
  ]

  const handleCreate = async (e) => {
    e.preventDefault()
    const result = await createRatePlan(toPayload(form))
    if (!result.error) { setOpen(false); setForm(EMPTY) }
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    const result = await updateRatePlan({ id: editTarget.id, ...toPayload(form) })
    if (!result.error) setEditTarget(null)
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" startIcon={<Add />} onClick={() => { setForm(EMPTY); setOpen(true) }}>Add Rate Plan</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} />

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Rate Plan</DialogTitle>
        <Box component="form" onSubmit={handleCreate}>
          <DialogContent><RatePlanForm form={form} setForm={setForm} roomTypes={roomTypes} /></DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={creating}>Add</Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog open={Boolean(editTarget)} onClose={() => setEditTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Rate Plan</DialogTitle>
        <Box component="form" onSubmit={handleUpdate}>
          <DialogContent><RatePlanForm form={form} setForm={setForm} roomTypes={roomTypes} /></DialogContent>
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
          <Button color="error" disabled={deleting} onClick={async () => { await deleteRatePlan(deleteTarget.id); setDeleteTarget(null) }}>Delete</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
