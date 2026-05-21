import React from 'react'
import { useNavigate, useParams, Link as RouterLink } from 'react-router-dom'
import { Box, Button, Paper, Typography, Grid, Chip } from '@mui/material'
import { ArrowBack } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetPaymentQuery } from '../../../features/payments/paymentsApi'

const STATUS_COLORS = { pending: 'warning', completed: 'success', failed: 'error', refunded: 'info' }

export default function PaymentDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: payment, isLoading, error } = useGetPaymentQuery(id)

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!payment) return null

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/admin/payments')}>Back</Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {(payment.status === 'pending' || payment.status === 'processing') && (
            <Button variant="outlined" component={RouterLink} to={`/payments/${id}/verify`}>Verify</Button>
          )}
          {payment.status === 'completed' && (
            <Button variant="outlined" color="warning" component={RouterLink} to={`/admin/refunds/new?payment=${id}`}>Issue Refund</Button>
          )}
        </Box>
      </Box>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Typography variant="h5">Payment #{payment.id}</Typography>
          <Chip label={payment.status} color={STATUS_COLORS[payment.status] || 'default'} />
        </Box>
        <Grid container spacing={2}>
          {[
            ['Booking', payment.booking],
            ['Guest', payment.guest_name || payment.guest],
            ['Amount', `€${Number(payment.amount || 0).toFixed(2)}`],
            ['Method', payment.payment_method],
            ['Transaction ID', payment.transaction_id || '—'],
            ['Date', payment.created_at ? new Date(payment.created_at).toLocaleDateString() : '—'],
          ].map(([label, val]) => (
            <Grid item xs={12} sm={6} md={4} key={label}>
              <Typography variant="caption" color="text.secondary">{label}</Typography>
              <Typography variant="body1">{val || '—'}</Typography>
            </Grid>
          ))}
          {payment.notes && <Grid item xs={12}><Typography variant="caption" color="text.secondary">Notes</Typography><Typography>{payment.notes}</Typography></Grid>}
        </Grid>
        {payment.invoice && (
          <Box sx={{ mt: 2 }}>
            <Button component={RouterLink} to={`/admin/invoices/${payment.invoice}`} variant="text">View Invoice →</Button>
          </Box>
        )}
      </Paper>
    </AppLayout>
  )
}
