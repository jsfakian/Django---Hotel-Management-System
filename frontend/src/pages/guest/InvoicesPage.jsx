import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Chip } from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import DataTable from '../../components/common/DataTable'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetInvoicesQuery } from '../../features/payments/paymentsApi'

const STATUS_COLORS = { draft: 'default', sent: 'info', paid: 'success', overdue: 'error', cancelled: 'warning' }
const columns = [
  { field: 'invoice_number', headerName: 'Invoice #', width: 140 },
  { field: 'booking', headerName: 'Booking', width: 100 },
  { field: 'total_amount', headerName: 'Total (€)', width: 120, renderCell: (r) => `€${Number(r.total_amount || r.total || 0).toFixed(2)}` },
  { field: 'status', headerName: 'Status', width: 120, renderCell: (r) => <Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} /> },
  { field: 'created_at', headerName: 'Date', width: 120, renderCell: (r) => r.created_at ? new Date(r.created_at).toLocaleDateString() : '—' },
]

export default function InvoicesPage() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useGetInvoicesQuery()
  const rows = data?.results || data || []

  return (
    <AppLayout>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={(r) => navigate(`/guest/invoices/${r.id}`)} />
    </AppLayout>
  )
}
