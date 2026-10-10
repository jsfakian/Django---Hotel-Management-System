import React, { useState } from 'react'
import { Box, Button, Chip, Typography, Tooltip } from '@mui/material'
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
  useValidateChannelMappingsMutation,
} from '../../../features/channels/channelsApi'
import {
  ChannelCreateDialog,
  ChannelEditDialog,
  ChannelDeleteDialog,
} from './ChannelDialogs'
import ChannelHealthDialog from './ChannelHealthDialog'
import {
  EMPTY_CHANNEL_FORM,
  channelLabel,
  parseMappingConfig,
  withDualMappingKeys,
  buildChannelPayload,
  formFromChannel,
} from './channelFormUtils'

function HealthCell({ row, onOpen }) {
  const errors = row.error_count ?? 0
  const lastSync = row.last_sync_at ? new Date(row.last_sync_at).toLocaleString() : '—'
  return (
    <Tooltip title={row.last_error || 'Click for health detail'} arrow>
      <Box
        onClick={(e) => { e.stopPropagation(); onOpen(row) }}
        sx={{ cursor: 'pointer' }}
      >
        <Chip
          size="small"
          label={errors > 0 ? `${errors} errors` : 'OK'}
          color={errors > 0 ? 'error' : 'success'}
          variant={errors > 0 ? 'filled' : 'outlined'}
        />
        <Typography variant="caption" display="block" color="text.secondary">{lastSync}</Typography>
      </Box>
    </Tooltip>
  )
}

function useChannelPageState() {
  const [newOpen, setNewOpen] = useState(false)
  const [editTarget, setEditTarget] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [healthTarget, setHealthTarget] = useState(null)
  const [form, setForm] = useState(EMPTY_CHANNEL_FORM)
  const [editForm, setEditForm] = useState(EMPTY_CHANNEL_FORM)
  const [formError, setFormError] = useState(null)
  const [validation, setValidation] = useState(null)
  const { data, isLoading, error } = useGetChannelsQuery()
  const [createChannel, { isLoading: creating }] = useCreateChannelMutation()
  const [updateChannel, { isLoading: updating }] = useUpdateChannelMutation()
  const [deleteChannel, { isLoading: deleting }] = useDeleteChannelMutation()
  const [syncAvailability] = useSyncChannelAvailabilityMutation()
  const [validateMappings, { isLoading: validating }] = useValidateChannelMappingsMutation()
  return {
    newOpen, setNewOpen, editTarget, setEditTarget, deleteTarget, setDeleteTarget,
    healthTarget, setHealthTarget,
    form, setForm, editForm, setEditForm, formError, setFormError, validation, setValidation,
    data, isLoading, error, createChannel, creating, updateChannel, updating,
    deleteChannel, deleting, syncAvailability, validateMappings, validating,
  }
}

export default function ChannelsListPage() {
  const s = useChannelPageState()
  const rows = s.data?.results || s.data || []

  const runValidate = async () => {
    if (!s.editTarget?.id) return
    s.setFormError(null)
    const result = await s.validateMappings({
      id: s.editTarget.id,
      mapping_config: withDualMappingKeys(parseMappingConfig(s.editForm.mapping_config)),
    })
    if (result.error) {
      s.setFormError(result.error)
      s.setValidation(null)
    } else {
      s.setValidation(result.data)
    }
  }

  const columns = [
    { field: 'channel_name', headerName: 'Channel', width: 140, renderCell: (r) => channelLabel(r.channel_name) },
    { field: 'property_name', headerName: 'Property', width: 140, renderCell: (r) => r.property_name || r.property },
    { field: 'account_id', headerName: 'Account', width: 120 },
    { field: 'is_active', headerName: 'Status', width: 90, renderCell: (r) => <Chip size="small" label={r.is_active ? 'Active' : 'Off'} color={r.is_active ? 'success' : 'default'} /> },
    { field: 'sync_enabled', headerName: 'Sync', width: 80, renderCell: (r) => (r.sync_enabled ? 'On' : 'Off') },
    {
      field: 'health',
      headerName: 'Health',
      width: 160,
      renderCell: (r) => <HealthCell row={r} onOpen={s.setHealthTarget} />,
    },
    {
      field: 'actions', headerName: '', width: 220,
      renderCell: (r) => (
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Button size="small" startIcon={<Sync />} onClick={(e) => { e.stopPropagation(); s.syncAvailability(r.id) }}>Sync</Button>
          <Button size="small" startIcon={<Edit />} onClick={(e) => { e.stopPropagation(); s.setEditForm(formFromChannel(r)); s.setEditTarget(r); s.setFormError(null); s.setValidation(null) }}>Edit</Button>
          <Button size="small" color="error" onClick={(e) => { e.stopPropagation(); s.setDeleteTarget(r) }}>Delete</Button>
        </Box>
      ),
    },
  ]

  const handleCreate = async (e) => {
    e.preventDefault()
    s.setFormError(null)
    const result = await s.createChannel(buildChannelPayload(s.form))
    if (!result.error) { s.setNewOpen(false); s.setForm(EMPTY_CHANNEL_FORM) }
    else s.setFormError(result.error)
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    s.setFormError(null)
    const payload = buildChannelPayload(s.editForm)
    if (!s.editForm.api_key) delete payload.api_key
    if (!s.editForm.api_secret) delete payload.api_secret
    const result = await s.updateChannel({ id: s.editTarget.id, ...payload })
    if (!result.error) s.setEditTarget(null)
    else s.setFormError(result.error)
  }

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" startIcon={<Add />} onClick={() => { s.setForm(EMPTY_CHANNEL_FORM); s.setFormError(null); s.setNewOpen(true) }}>
          Add Channel
        </Button>
      </Box>
      {s.error && <ErrorAlert error={s.error} />}
      <DataTable columns={columns} rows={rows} loading={s.isLoading} />
      <ChannelCreateDialog open={s.newOpen} onClose={() => s.setNewOpen(false)} form={s.form} setForm={s.setForm} formError={s.formError} onSubmit={handleCreate} creating={s.creating} />
      <ChannelEditDialog open={Boolean(s.editTarget)} onClose={() => s.setEditTarget(null)} title={`Edit ${channelLabel(s.editTarget?.channel_name)}`} form={s.editForm} setForm={s.setEditForm} formError={s.formError} onSubmit={handleUpdate} updating={s.updating} channelId={s.editTarget?.id} onValidate={runValidate} validating={s.validating} validation={s.validation} />
      <ChannelDeleteDialog open={Boolean(s.deleteTarget)} onClose={() => s.setDeleteTarget(null)} channelName={s.deleteTarget?.channel_name} onConfirm={async () => { await s.deleteChannel(s.deleteTarget.id); s.setDeleteTarget(null) }} deleting={s.deleting} />
      <ChannelHealthDialog
        open={Boolean(s.healthTarget)}
        channelId={s.healthTarget?.id}
        channelLabel={channelLabel(s.healthTarget?.channel_name)}
        onClose={() => s.setHealthTarget(null)}
      />
    </AppLayout>
  )
}
