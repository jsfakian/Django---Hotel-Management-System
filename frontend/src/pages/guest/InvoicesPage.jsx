import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Typography, Chip, Card, CardActionArea, CardContent, Grid } from '@mui/material'
import { Receipt } from '@mui/icons-material'
import GuestLayout from '../../components/layout/GuestLayout'
import ErrorAlert from '../../components/common/ErrorAlert'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import EmptyState from '../../components/common/EmptyState'
import { useGetInvoicesQuery } from '../../features/payments/paymentsApi'

const STATUS_COLORS = {
  draft: 'default',
  sent: 'info',
  paid: 'success',
  overdue: 'error',
  cancelled: 'warning',
}

export default function InvoicesPage() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useGetInvoicesQuery()
  const rows = data?.results || data || []

  return (
    <GuestLayout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontFamily: '"Fraunces", Georgia, serif' }}>
          Invoices
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Clear statements for your stays — open any invoice for details and download
        </Typography>
      </Box>

      {error && <ErrorAlert error={error} />}
      {isLoading ? (
        <LoadingSpinner />
      ) : rows.length === 0 ? (
        <EmptyState
          title="No invoices yet"
          description="Invoices appear here after a stay is billed."
          icon={<Receipt fontSize="large" />}
        />
      ) : (
        <Grid container spacing={2}>
          {rows.map((inv) => (
            <Grid item xs={12} sm={6} key={inv.id}>
              <Card>
                <CardActionArea onClick={() => navigate(`/guest/invoices/${inv.id}`)}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography fontWeight={700}>
                        {inv.invoice_number || `Invoice #${inv.id}`}
                      </Typography>
                      <Chip
                        size="small"
                        label={inv.status}
                        color={STATUS_COLORS[inv.status] || 'default'}
                        sx={{ textTransform: 'capitalize' }}
                      />
                    </Box>
                    <Typography variant="h6">
                      €{Number(inv.total_amount || inv.total || 0).toFixed(2)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {inv.created_at
                        ? new Date(inv.created_at).toLocaleDateString('en-GB')
                        : '—'}
                      {inv.booking ? ` · Booking ${inv.booking}` : ''}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </GuestLayout>
  )
}
