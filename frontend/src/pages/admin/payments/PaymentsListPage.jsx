import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, FormControl, InputLabel, Select, MenuItem, TextField, Chip } from '@mui/material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetPaymentsQuery } from '../../../features/payments/paymentsApi'

const STATUS_COLORS = { pending: 'warning', completed: 'success', failed: 'error', refunded: 'info' }
const columns = [
  { field: 'id', headerName: 'ID', width: 70 },
  { field: 'booking', headerName: 'Booking ID', width: 100 },
  { field: 'guest_name', headerName: 'Guest', width: 180 },
  { field: 'amount', headerName: 'Amount (€)', width: 120, renderCell: (r) => `€${Number(r.amount || 0).toFixed(2)}` },
  { field: 'payment_method', headerName: 'Method', width: 120 },
  { field: 'status', headerName: 'Status', width: 130, renderCell: (r) => <Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} /> },
  { field: 'created_at', headerName: 'Date', width: 120, renderCell: (r) => r.created_at ? new Date(r.created_at).toLocaleDateString() : '—' },
]

export default function PaymentsListPage() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('')
  const [dateAfter, setDateAfter] = useState('')
  const [dateBefore, setDateBefore] = useState('')
  const { data, isLoading, error } = useGetPaymentsQuery({ status: status || undefined, date_after: dateAfter || undefined, date_before: dateBefore || undefined })
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Status</InputLabel>
          <Select value={status} label="Status" onChange={(e) => setStatus(e.target.value)}>
            {['', 'pending', 'completed', 'failed', 'refunded'].map((s) => <MenuItem key={s} value={s}>{s || 'All'}</MenuItem>)}
          </Select>
        </FormControl>
        <TextField size="small" label="From" type="date" InputLabelProps={{ shrink: true }} value={dateAfter} onChange={(e) => setDateAfter(e.target.value)} />
        <TextField size="small" label="To" type="date" InputLabelProps={{ shrink: true }} value={dateBefore} onChange={(e) => setDateBefore(e.target.value)} />
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={(r) => navigate(`/admin/payments/${r.id}`)} />
    </AppLayout>
  )
}
