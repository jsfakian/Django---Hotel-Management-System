import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, Paper, Typography, Grid, Chip, Table, TableBody, TableCell, TableHead, TableRow, Divider, Alert } from '@mui/material'
import { ArrowBack, PictureAsPdf, Send } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetInvoiceQuery, useTransmitInvoiceToMydataMutation } from '../../../features/payments/paymentsApi'
import { downloadFile } from '../../../services/downloadFile'

const STATUS_COLORS = { draft: 'default', sent: 'info', paid: 'success', overdue: 'error', cancelled: 'warning' }

export default function InvoiceDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [msg, setMsg] = useState(null)
  const [pdfLoading, setPdfLoading] = useState(false)
  const { data: invoice, isLoading, error } = useGetInvoiceQuery(id)
  const [transmit, { isLoading: transmitting }] = useTransmitInvoiceToMydataMutation()

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!invoice) return null

  const lineItems = invoice.line_items || invoice.items || []

  const handlePdf = async () => {
    setPdfLoading(true)
    try {
      await downloadFile(`/payments/invoices/${id}/pdf/`, `invoice-${invoice.invoice_number || id}.pdf`)
    } catch {
      setMsg({ type: 'error', text: 'PDF download failed.' })
    } finally {
      setPdfLoading(false)
    }
  }

  const handleMyData = async () => {
    const result = await transmit(id)
    if (result.error) {
      setMsg({ type: 'error', text: 'MyData transmission failed.' })
    } else {
      setMsg({ type: 'success', text: 'Invoice transmitted to AADE MyData successfully.' })
    }
  }

  return (
    <AppLayout>
      {msg && <Alert severity={msg.type} sx={{ mb: 2 }} onClose={() => setMsg(null)}>{msg.text}</Alert>}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3, flexWrap: 'wrap', gap: 1 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate(-1)}>Back</Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button startIcon={<PictureAsPdf />} variant="outlined" onClick={handlePdf} disabled={pdfLoading}>
            {pdfLoading ? 'Downloading…' : 'Download PDF'}
          </Button>
          {!invoice.mydata_sent && (
            <Button startIcon={<Send />} variant="contained" color="secondary" onClick={handleMyData} disabled={transmitting}>
              {transmitting ? 'Transmitting…' : 'Send to MyData (AADE)'}
            </Button>
          )}
        </Box>
      </Box>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 3 }}>
          <Box>
            <Typography variant="h5">Invoice {invoice.invoice_number}</Typography>
            <Typography color="text.secondary">Booking #{invoice.booking}</Typography>
          </Box>
          <Box sx={{ textAlign: 'right' }}>
            <Chip label={invoice.status} color={STATUS_COLORS[invoice.status] || 'default'} sx={{ mb: 1 }} />
            <br />
            <Chip size="small" label={invoice.mydata_sent ? 'MyData Sent' : 'MyData Pending'} color={invoice.mydata_sent ? 'success' : 'warning'} />
          </Box>
        </Box>
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[
            ['Guest', invoice.guest_name || invoice.guest],
            ['Issue Date', invoice.issue_date ? new Date(invoice.issue_date).toLocaleDateString() : '—'],
            ['Due Date', invoice.due_date ? new Date(invoice.due_date).toLocaleDateString() : '—'],
          ].map(([label, val]) => (
            <Grid item xs={12} sm={4} key={label}>
              <Typography variant="caption" color="text.secondary">{label}</Typography>
              <Typography>{val || '—'}</Typography>
            </Grid>
          ))}
        </Grid>
        {lineItems.length > 0 && (
          <>
            <Typography variant="h6" sx={{ mb: 1 }}>Line Items</Typography>
            <Table size="small" sx={{ mb: 3 }}>
              <TableHead>
                <TableRow>{['Description', 'Qty', 'Unit Price', 'Total'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow>
              </TableHead>
              <TableBody>
                {lineItems.map((item, i) => (
                  <TableRow key={i}>
                    <TableCell>{item.description}</TableCell>
                    <TableCell>{item.quantity}</TableCell>
                    <TableCell>€{Number(item.unit_price || 0).toFixed(2)}</TableCell>
                    <TableCell>€{Number(item.total || 0).toFixed(2)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}
        <Divider sx={{ my: 2 }} />
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Box sx={{ minWidth: 240 }}>
            {[['Subtotal', invoice.subtotal], ['Tax', invoice.tax_amount], ['Total', invoice.total_amount || invoice.total]].map(([label, val]) => (
              <Box key={label} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                <Typography fontWeight={label === 'Total' ? 700 : 400}>{label}</Typography>
                <Typography fontWeight={label === 'Total' ? 700 : 400}>€{Number(val || 0).toFixed(2)}</Typography>
              </Box>
            ))}
          </Box>
        </Box>
      </Paper>
    </AppLayout>
  )
}
