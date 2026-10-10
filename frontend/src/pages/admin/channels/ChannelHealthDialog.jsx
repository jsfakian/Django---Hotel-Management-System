import React from 'react'
import {
  Box, Button, CircularProgress, Dialog, DialogActions, DialogContent,
  DialogTitle, Typography,
} from '@mui/material'
import { useGetChannelHealthQuery } from '../../../features/channels/channelsApi'
import ErrorAlert from '../../../components/common/ErrorAlert'

function lagLabel(lastSyncAt) {
  if (!lastSyncAt) return '—'
  const ms = Date.now() - new Date(lastSyncAt).getTime()
  if (Number.isNaN(ms) || ms < 0) return '—'
  const mins = Math.round(ms / 60000)
  if (mins < 60) return `${mins} min`
  const hours = Math.round(mins / 60)
  if (hours < 48) return `${hours} h`
  return `${Math.round(hours / 24)} d`
}

function HealthRow({ label, value }) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.75, gap: 2 }}>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
      <Typography variant="body2" fontWeight={500} sx={{ textAlign: 'right', wordBreak: 'break-word' }}>
        {value ?? '—'}
      </Typography>
    </Box>
  )
}

export default function ChannelHealthDialog({ open, channelId, channelLabel, onClose }) {
  const { data, isLoading, error } = useGetChannelHealthQuery(channelId, {
    skip: !open || !channelId,
  })

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Health — {channelLabel || channelId}</DialogTitle>
      <DialogContent>
        {isLoading && (
          <Box sx={{ py: 3, textAlign: 'center' }}><CircularProgress size={28} /></Box>
        )}
        {error && <ErrorAlert error={error} />}
        {data && !isLoading && (
          <Box>
            <HealthRow label="Status" value={data.healthy ? 'Healthy' : 'Attention'} />
            <HealthRow label="Sync lag" value={lagLabel(data.last_sync_at)} />
            <HealthRow
              label="Last sync"
              value={data.last_sync_at ? new Date(data.last_sync_at).toLocaleString() : '—'}
            />
            <HealthRow label="Webhook logs" value={data.webhook_log_count} />
            <HealthRow label="Pending syncs" value={data.pending_sync_count} />
            <HealthRow label="Error count" value={data.error_count} />
            <HealthRow label="Latest sync status" value={data.latest_sync_status} />
            <HealthRow label="Last error" value={data.last_error || 'None'} />
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  )
}
