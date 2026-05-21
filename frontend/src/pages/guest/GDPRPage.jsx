import React, { useState } from 'react'
import {
  Box, Paper, Typography, Button, Alert, Divider, TextField,
  Dialog, DialogTitle, DialogContent, DialogActions, LinearProgress, Chip,
} from '@mui/material'
import { Download, DeleteForever, Shield } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import { useRequestDataExportMutation, useRequestDataDeletionMutation, useCheckExportStatusQuery } from '../../features/gdpr/gdprApi'
import axiosInstance from '../../services/axiosInstance'

export default function GDPRPage() {
  const [exportMsg, setExportMsg] = useState(null)
  const [taskId, setTaskId] = useState(null)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleteReason, setDeleteReason] = useState('')
  const [deleteMsg, setDeleteMsg] = useState(null)
  const [downloading, setDownloading] = useState(false)

  const [requestExport, { isLoading: exporting }] = useRequestDataExportMutation()
  const [requestDeletion, { isLoading: deleting }] = useRequestDataDeletionMutation()
  const { data: statusData } = useCheckExportStatusQuery(taskId, { skip: !taskId, pollingInterval: 3000 })

  const handleExport = async () => {
    setExportMsg(null)
    const result = await requestExport()
    if (result.error) {
      setExportMsg({ type: 'error', text: 'Failed to request data export.' })
    } else {
      const tid = result.data?.task_id
      if (tid) {
        setTaskId(tid)
        setExportMsg({ type: 'info', text: 'Export requested. We will notify you when ready.' })
      } else {
        setExportMsg({ type: 'success', text: 'Your data export is ready to download.' })
      }
    }
  }

  const handleDownload = async () => {
    setDownloading(true)
    try {
      const response = await axiosInstance.get('/gdpr/download-export/', { responseType: 'blob' })
      const href = URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = href
      link.download = 'my-data-export.json'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(href)
    } catch {
      setExportMsg({ type: 'error', text: 'Download failed. Please try again.' })
    } finally {
      setDownloading(false)
    }
  }

  const handleDelete = async () => {
    const result = await requestDeletion({ reason: deleteReason })
    if (result.error) {
      setDeleteMsg({ type: 'error', text: 'Failed to submit deletion request.' })
    } else {
      setDeleteMsg({ type: 'success', text: 'Deletion request submitted. You will be contacted within 30 days.' })
      setDeleteOpen(false)
    }
  }

  const exportReady = statusData?.status === 'completed' || (!taskId && exportMsg?.type === 'success')

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <Shield color="primary" />
        <Typography variant="h5">Privacy & Data Rights</Typography>
      </Box>

      {/* Data Export — Article 15 / 20 */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Export My Data</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Under GDPR Articles 15 and 20, you have the right to receive a copy of your personal data in a portable format.
        </Typography>
        {exportMsg && <Alert severity={exportMsg.type} sx={{ mb: 2 }} onClose={() => setExportMsg(null)}>{exportMsg.text}</Alert>}
        {deleteMsg && <Alert severity={deleteMsg.type} sx={{ mb: 2 }} onClose={() => setDeleteMsg(null)}>{deleteMsg.text}</Alert>}
        {taskId && statusData && (
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Typography variant="body2">Export status:</Typography>
              <Chip size="small" label={statusData.status} color={statusData.status === 'completed' ? 'success' : 'info'} />
            </Box>
            {statusData.status !== 'completed' && <LinearProgress />}
          </Box>
        )}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button variant="contained" startIcon={<Download />} onClick={handleExport} disabled={exporting}>
            {exporting ? 'Requesting…' : 'Request Export'}
          </Button>
          {exportReady && (
            <Button variant="outlined" startIcon={<Download />} onClick={handleDownload} disabled={downloading}>
              {downloading ? 'Downloading…' : 'Download My Data'}
            </Button>
          )}
        </Box>
      </Paper>

      <Divider sx={{ my: 3 }} />

      {/* Right to Erasure — Article 17 */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom color="error">Request Data Deletion</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Under GDPR Article 17, you have the right to request erasure of your personal data.
          This will permanently delete your account and all associated data. This action cannot be undone.
        </Typography>
        <Button variant="outlined" color="error" startIcon={<DeleteForever />} onClick={() => setDeleteOpen(true)}>
          Request Account Deletion
        </Button>
      </Paper>

      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Request Data Deletion</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This will permanently delete your account. You will lose all booking history and data.
          </Alert>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Reason (optional)"
            value={deleteReason}
            onChange={(e) => setDeleteReason(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteOpen(false)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={handleDelete} disabled={deleting}>
            {deleting ? 'Submitting…' : 'Confirm Deletion Request'}
          </Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
