import React, { useState } from 'react'
import {
  Box, Button, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Grid, MenuItem, Chip, FormControlLabel, Switch, Typography, Tooltip,
} from '@mui/material'
import { Add, Sync, Edit } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import {
  useGetChannelsQuery,
  useCreateChannelMutation,
  useUpdateChannelMutation,
  useDeleteChannelMutation,
  useSyncChannelAvailabilityMutation,
} from '../../../features/channels/channelsApi'

const CHANNEL_CHOICES = [
  'booking_com', 'trivago', 'airbnb', 'expedia', 'agoda', 'vrbo', 'ical',
  'booking_buddy', 'hotwire', 'travelocity', 'priceline', 'orbitz', 'kayak',
  'hostelworld', 'ctrip', 'custom',
]

const EMPTY_FORM = {
  channel_name: '',
  property: '',
  account_id: '',
  api_key: '',
  api_secret: '',
  mapping_config: '{}',
  is_active: true,
  sync_enabled: true,
}

function channelLabel(value) {
  return (value || '').replace(/_/g, '.')
}

function parseMappingConfig(raw) {
  const text = (raw || '{}').trim() || '{}'
  return JSON.parse(text)
}

function buildPayload(form) {
  return {
    channel_name: form.channel_name,
    property: Number(form.property),
    account_id: form.account_id,
    api_key: form.api_key || undefined,
    api_secret: form.api_secret || undefined,
    mapping_config: parseMappingConfig(form.mapping_config),
    is_active: Boolean(form.is_active),
    sync_enabled: Boolean(form.sync_enabled),
  }
}

function HealthCell({ row }) {
  const errors = row.error_count ?? 0
  const lastSync = row.last_sync_at ? new Date(row.last_sync_at).toLocaleString() : '—'
  const chip = (
    <Chip
      size="small"
      label={errors > 0 ? `${errors} errors` : 'OK'}
      color={errors > 0 ? 'error' : 'success'}
      variant={errors > 0 ? 'filled' : 'outlined'}
    />
  )
  if (!row.last_error && errors === 0) {
    return (
      <Box>
        {chip}
        <Typography variant="caption" display="block" color="text.secondary">{lastSync}</Typography>
      </Box>
    )
  }
  return (
    <Tooltip title={row.last_error || 'No error message'} arrow>
      <Box>
        {chip}
        <Typography variant="caption" display="block" color="text.secondary">{lastSync}</Typography>
      </Box>
    </Tooltip>
  )
}

function ChannelFormFields({ form, setForm, isEdit }) {
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
  return (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={6}>
        <TextField select fullWidth required label="Channel" value={form.channel_name} onChange={set('channel_name')} disabled={isEdit}>
          {CHANNEL_CHOICES.map((c) => (
            <MenuItem key={c} value={c}>{channelLabel(c)}</MenuItem>
          ))}
        </TextField>
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField fullWidth required label="Property ID" type="number" value={form.property} onChange={set('property')} disabled={isEdit} />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField fullWidth required label="Account ID" value={form.account_id} onChange={set('account_id')} />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField fullWidth label="API Key" value={form.api_key} onChange={set('api_key')} helperText={isEdit ? 'Leave blank to keep current' : undefined} required={!isEdit} />
      </Grid>
      <Grid item xs={12} sm={6}>
        <TextField fullWidth label="API Secret" value={form.api_secret} onChange={set('api_secret')} helperText={isEdit ? 'Leave blank to keep current' : 'Optional'} />
      </Grid>
      <Grid item xs={12} sm={6} sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <FormControlLabel control={<Switch checked={Boolean(form.is_active)} onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))} />} label="Active" />
        <FormControlLabel control={<Switch checked={Boolean(form.sync_enabled)} onChange={(e) => setForm((f) => ({ ...f, sync_enabled: e.target.checked }))} />} label="Sync enabled" />
      </Grid>
      <Grid item xs={12}>
        <TextField
          fullWidth
          multiline
          minRows={4}
          label="Mapping config (JSON)"
          value={form.mapping_config}
          onChange={set('mapping_config')}
          helperText='e.g. {"room_mappings":{},"rate_mappings":{}}'
        />
      </Grid>
    </Grid>
  )
}

function formFromChannel(row) {
  return {
    channel_name: row.channel_name || '',
    property: row.property || '',
    account_id: row.account_id || '',
    api_key: '',
    api_secret: '',
    mapping_config: JSON.stringify(row.mapping_config || {}, null, 2),
    is_active: row.is_active !== false,
    sync_enabled: row.sync_enabled !== false,
  }
}

export default function ChannelsListPage() {
  const [newOpen, setNewOpen] = useState(false)
  const [editTarget, setEditTarget] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [editForm, setEditForm] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState(null)

  const { data, isLoading, error } = useGetChannelsQuery()
  const [createChannel, { isLoading: creating }] = useCreateChannelMutation()
  const [updateChannel, { isLoading: updating }] = useUpdateChannelMutation()
  const [deleteChannel, { isLoading: deleting }] = useDeleteChannelMutation()
  const [syncAvailability] = useSyncChannelAvailabilityMutation()

  const rows = data?.results || data || []

  const columns = [
    { field: 'channel_name', headerName: 'Channel', width: 140, renderCell: (r) => channelLabel(r.channel_name) },
    { field: 'property_name', headerName: 'Property', width: 140, renderCell: (r) => r.property_name || r.property },
    { field: 'account_id', headerName: 'Account', width: 120 },
    { field: 'is_active', headerName: 'Status', width: 90, renderCell: (r) => <Chip size="small" label={r.is_active ? 'Active' : 'Off'} color={r.is_active ? 'success' : 'default'} /> },
    { field: 'sync_enabled', headerName: 'Sync', width: 80, renderCell: (r) => (r.sync_enabled ? 'On' : 'Off') },
    { field: 'health', headerName: 'Health', width: 160, renderCell: (r) => <HealthCell row={r} /> },
    {
      field: 'actions',
      headerName: '',
      width: 220,
      renderCell: (r) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Button size="small" startIcon={<Sync />} onClick={(e) => { e.stopPropagation(); syncAvailability(r.id) }}>Sync</Button>
          <Button size="small" startIcon={<Edit />} onClick={(e) => { e.stopPropagation(); setEditForm(formFromChannel(r)); setEditTarget(r); setFormError(null) }}>Edit</Button>
          <Button size="small" color="error" onClick={(e) => { e.stopPropagation(); setDeleteTarget(r) }}>Delete</Button>
        </Box>
      ),
    },
  ]

  const handleCreate = async (e) => {
    e.preventDefault()
    setFormError(null)
    try {
      const result = await createChannel(buildPayload(form))
      if (!result.error) {
        setNewOpen(false)
        setForm(EMPTY_FORM)
      } else {
        setFormError(result.error)
      }
    } catch (err) {
      setFormError({ data: { detail: err.message } })
    }
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    setFormError(null)
    try {
      const payload = buildPayload(editForm)
      if (!editForm.api_key) delete payload.api_key
      if (!editForm.api_secret) delete payload.api_secret
      const result = await updateChannel({ id: editTarget.id, ...payload })
      if (!result.error) {
        setEditTarget(null)
      } else {
        setFormError(result.error)
      }
    } catch (err) {
      setFormError({ data: { detail: err.message } })
    }
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" startIcon={<Add />} onClick={() => { setForm(EMPTY_FORM); setFormError(null); setNewOpen(true) }}>
          Add Channel
        </Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} />

      <Dialog open={newOpen} onClose={() => setNewOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add OTA Channel</DialogTitle>
        <Box component="form" onSubmit={handleCreate}>
          <DialogContent>
            {formError && <ErrorAlert error={formError} />}
            <ChannelFormFields form={form} setForm={setForm} />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setNewOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={creating}>Add</Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog open={Boolean(editTarget)} onClose={() => setEditTarget(null)} maxWidth="md" fullWidth>
        <DialogTitle>Edit {channelLabel(editTarget?.channel_name)}</DialogTitle>
        <Box component="form" onSubmit={handleUpdate}>
          <DialogContent>
            {formError && <ErrorAlert error={formError} />}
            <ChannelFormFields form={editForm} setForm={setEditForm} isEdit />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditTarget(null)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={updating}>Save</Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Remove &quot;{deleteTarget?.channel_name}&quot; channel?</DialogTitle>
        <DialogContent>This will stop syncing bookings from this channel.</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button color="error" onClick={async () => { await deleteChannel(deleteTarget.id); setDeleteTarget(null) }} disabled={deleting}>Remove</Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
