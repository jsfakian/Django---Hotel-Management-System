import React from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, Paper, Typography, Grid, Chip, Table, TableBody, TableCell, TableHead, TableRow, Divider } from '@mui/material'
import { ArrowBack, Print } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetInvoiceQuery } from '../../features/payments/paymentsApi'

const STATUS_COLORS = { draft: 'default', sent: 'info', paid: 'success', overdue: 'error', cancelled: 'warning' }

export default function InvoiceDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: invoice, isLoading, error } = useGetInvoiceQuery(id)

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!invoice) return null

  const lineItems = invoice.line_items || invoice.items || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/guest/invoices')}>Back</Button>
        <Button startIcon={<Print />} variant="outlined" onClick={() => window.print()}>Print</Button>
      </Box>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
          <Typography variant="h5">Invoice {invoice.invoice_number}</Typography>
          <Chip label={invoice.status} color={STATUS_COLORS[invoice.status] || 'default'} />
        </Box>
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[['Booking', invoice.booking], ['Issue Date', invoice.issue_date ? new Date(invoice.issue_date).toLocaleDateString() : '—'], ['Due Date', invoice.due_date ? new Date(invoice.due_date).toLocaleDateString() : '—']].map(([label, val]) => (
            <Grid item xs={12} sm={4} key={label}><Typography variant="caption" color="text.secondary">{label}</Typography><Typography>{val || '—'}</Typography></Grid>
          ))}
        </Grid>
        {lineItems.length > 0 && (
          <Table size="small" sx={{ mb: 3 }}>
            <TableHead><TableRow>{['Description', 'Qty', 'Unit Price', 'Total'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
            <TableBody>{lineItems.map((item, i) => <TableRow key={i}><TableCell>{item.description}</TableCell><TableCell>{item.quantity}</TableCell><TableCell>€{Number(item.unit_price || 0).toFixed(2)}</TableCell><TableCell>€{Number(item.total || 0).toFixed(2)}</TableCell></TableRow>)}</TableBody>
          </Table>
        )}
        <Divider sx={{ my: 2 }} />
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Box sx={{ minWidth: 240 }}>
            {[['Subtotal', invoice.subtotal], ['Tax', invoice.tax_amount], ['Total', invoice.total_amount || invoice.total]].map(([label, val]) => (
              <Box key={label} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}><Typography fontWeight={label === 'Total' ? 700 : 400}>{label}</Typography><Typography fontWeight={label === 'Total' ? 700 : 400}>€{Number(val || 0).toFixed(2)}</Typography></Box>
            ))}
          </Box>
        </Box>
      </Paper>
    </AppLayout>
  )
}
