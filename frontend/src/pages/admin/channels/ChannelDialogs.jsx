import React from 'react'
import {
  Box, Button, Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, Grid, MenuItem, FormControlLabel, Switch,
} from '@mui/material'
import ErrorAlert from '../../../components/common/ErrorAlert'
import MappingMatrix from './MappingMatrix'
import { channelLabel } from './channelFormUtils'

const CHANNEL_CHOICES = [
  'booking_com', 'trivago', 'airbnb', 'expedia', 'agoda', 'vrbo', 'ical',
  'booking_buddy', 'hotwire', 'travelocity', 'priceline', 'orbitz', 'kayak',
  'hostelworld', 'ctrip', 'custom',
]

function ChannelFormFields({
  form, setForm, isEdit, channelId, onValidate, validating, validation,
}) {
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
        <MappingMatrix
          mappingConfigText={form.mapping_config}
          onMappingConfigChange={(text) => setForm((f) => ({ ...f, mapping_config: text }))}
          onValidate={channelId ? onValidate : undefined}
          validating={validating}
          validation={validation}
        />
      </Grid>
    </Grid>
  )
}

export function ChannelCreateDialog({
  open, onClose, form, setForm, formError, onSubmit, creating,
}) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Add OTA Channel</DialogTitle>
      <Box component="form" onSubmit={onSubmit}>
        <DialogContent>
          {formError && <ErrorAlert error={formError} />}
          <ChannelFormFields form={form} setForm={setForm} />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={creating}>Add</Button>
        </DialogActions>
      </Box>
    </Dialog>
  )
}

export function ChannelEditDialog({
  open, onClose, title, form, setForm, formError, onSubmit, updating,
  channelId, onValidate, validating, validation,
}) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <Box component="form" onSubmit={onSubmit}>
        <DialogContent>
          {formError && <ErrorAlert error={formError} />}
          <ChannelFormFields
            form={form}
            setForm={setForm}
            isEdit
            channelId={channelId}
            onValidate={onValidate}
            validating={validating}
            validation={validation}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={updating}>Save</Button>
        </DialogActions>
      </Box>
    </Dialog>
  )
}

export function ChannelDeleteDialog({
  open, onClose, channelName, onConfirm, deleting,
}) {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Remove &quot;{channelName}&quot; channel?</DialogTitle>
      <DialogContent>This will stop syncing bookings from this channel.</DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button color="error" onClick={onConfirm} disabled={deleting}>Remove</Button>
      </DialogActions>
    </Dialog>
  )
}
