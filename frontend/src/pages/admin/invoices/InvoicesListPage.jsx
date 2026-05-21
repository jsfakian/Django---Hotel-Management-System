import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, FormControl, InputLabel, Select, MenuItem, Chip } from '@mui/material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetInvoicesQuery } from '../../../features/payments/paymentsApi'

const STATUS_COLORS = { draft: 'default', sent: 'info', paid: 'success', overdue: 'error', cancelled: 'warning' }
const columns = [
  { field: 'invoice_number', headerName: 'Invoice #', width: 140 },
  { field: 'guest_name', headerName: 'Guest', width: 180 },
  { field: 'booking', headerName: 'Booking', width: 100 },
  { field: 'subtotal', headerName: 'Subtotal (€)', width: 120, renderCell: (r) => `€${Number(r.subtotal || 0).toFixed(2)}` },
  { field: 'tax_amount', headerName: 'Tax (€)', width: 100, renderCell: (r) => `€${Number(r.tax_amount || 0).toFixed(2)}` },
  { field: 'total_amount', headerName: 'Total (€)', width: 110, renderCell: (r) => `€${Number(r.total_amount || r.total || 0).toFixed(2)}` },
  { field: 'status', headerName: 'Status', width: 120, renderCell: (r) => <Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} /> },
  { field: 'mydata_sent', headerName: 'MyData', width: 90, renderCell: (r) => <Chip size="small" label={r.mydata_sent ? 'Sent' : 'Pending'} color={r.mydata_sent ? 'success' : 'warning'} /> },
  { field: 'created_at', headerName: 'Date', width: 110, renderCell: (r) => r.created_at ? new Date(r.created_at).toLocaleDateString() : '—' },
]

export default function InvoicesListPage() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('')
  const { data, isLoading, error } = useGetInvoicesQuery({ status: status || undefined })
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ mb: 2 }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Status</InputLabel>
          <Select value={status} label="Status" onChange={(e) => setStatus(e.target.value)}>
            {['', 'draft', 'sent', 'paid', 'overdue', 'cancelled'].map((s) => <MenuItem key={s} value={s}>{s || 'All'}</MenuItem>)}
          </Select>
        </FormControl>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={(r) => navigate(`/admin/invoices/${r.id}`)} />
    </AppLayout>
  )
}
