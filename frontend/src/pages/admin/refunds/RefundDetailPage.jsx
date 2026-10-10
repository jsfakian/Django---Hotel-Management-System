import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, Paper, Typography, Grid, Chip, Dialog, DialogTitle, DialogContent, DialogActions, Alert, TextField } from '@mui/material'
import { ArrowBack } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetRefundQuery, useUpdateRefundMutation } from '../../../features/refunds/refundsApi'

const STATUS_COLORS = { pending: 'warning', approved: 'success', rejected: 'error', processed: 'info' }

const DASH = '—'
const fmtDate = (v) => (v ? new Date(v).toLocaleDateString() : DASH)
const ACTION_LABELS = { approved: 'Approve', processed: 'Process', rejected: 'Reject' }
const ACTION_COLORS = { approved: 'success', processed: 'primary', rejected: 'error' }

function RefundFields({ refund }) {
  const fields = [
    ['Booking', refund.booking],
    ['Guest', refund.guest_name || refund.guest],
    ['Payment', refund.payment],
    ['Amount', `€${Number(refund.amount || 0).toFixed(2)}`],
    ['Requested', fmtDate(refund.created_at)],
    ['Processed', fmtDate(refund.processed_at)],
  ]
  return (
    <Grid container spacing={2} sx={{ mb: 3 }}>
      {fields.map(([label, val]) => (
        <Grid item xs={12} sm={6} md={4} key={label}>
          <Typography variant="caption" color="text.secondary">{label}</Typography>
          <Typography>{val || DASH}</Typography>
        </Grid>
      ))}
      <Grid item xs={12}><Typography variant="caption" color="text.secondary">Reason</Typography><Typography>{refund.reason}</Typography></Grid>
      {refund.admin_notes && <Grid item xs={12}><Typography variant="caption" color="text.secondary">Admin Notes</Typography><Typography>{refund.admin_notes}</Typography></Grid>}
    </Grid>
  )
}

function RefundActions({ status, onAction }) {
  if (status === 'pending') {
    return (
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Button variant="contained" color="success" onClick={() => onAction('approved')}>Approve</Button>
        <Button variant="outlined" color="error" onClick={() => onAction('rejected')}>Reject</Button>
      </Box>
    )
  }
  if (status === 'approved') {
    return (
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Button variant="contained" onClick={() => onAction('processed')}>Mark Processed</Button>
      </Box>
    )
  }
  return null
}

function RefundActionDialog({ action, refundId, reason, onReasonChange, onClose, onConfirm, updating }) {
  return (
    <Dialog open={Boolean(action)} onClose={onClose}>
      <DialogTitle>{ACTION_LABELS[action] || ACTION_LABELS.rejected} refund #{refundId}?</DialogTitle>
      <DialogContent>
        {action === 'rejected' ? (
          <TextField
            fullWidth
            multiline
            minRows={3}
            autoFocus
            margin="dense"
            label="Rejection reason"
            value={reason}
            onChange={(e) => onReasonChange(e.target.value)}
          />
        ) : (
          'This action will update the refund status.'
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button color={ACTION_COLORS[action] || 'error'} onClick={() => onConfirm(action)} disabled={updating}>
          Confirm
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default function RefundDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [dialog, setDialog] = useState(null)
  const [rejectionReason, setRejectionReason] = useState('')
  const [msg, setMsg] = useState('')
  const { data: refund, isLoading, error } = useGetRefundQuery(id)
  const [updateRefund, { isLoading: updating }] = useUpdateRefundMutation()

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!refund) return null

  const handleAction = async (status) => {
    const payload = { id, status }
    if (status === 'rejected') {
      payload.rejection_reason = rejectionReason
    }
    const result = await updateRefund(payload)
    if (!result.error) { setMsg(`Refund ${status}.`); setDialog(null) }
  }

  return (
    <AppLayout>
      <Button startIcon={<ArrowBack />} onClick={() => navigate('/admin/refunds')} sx={{ mb: 3 }}>Back</Button>
      {msg && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMsg('')}>{msg}</Alert>}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Typography variant="h5">Refund #{refund.id}</Typography>
          <Chip label={refund.status} color={STATUS_COLORS[refund.status] || 'default'} />
        </Box>
        <RefundFields refund={refund} />
        <RefundActions status={refund.status} onAction={setDialog} />
      </Paper>
      <RefundActionDialog
        action={dialog}
        refundId={refund.id}
        reason={rejectionReason}
        onReasonChange={setRejectionReason}
        onClose={() => setDialog(null)}
        onConfirm={handleAction}
        updating={updating}
      />
    </AppLayout>
  )
}
