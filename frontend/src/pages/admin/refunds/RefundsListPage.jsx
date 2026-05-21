import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, FormControl, InputLabel, Select, MenuItem, Chip } from '@mui/material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetRefundsQuery } from '../../../features/refunds/refundsApi'

const STATUS_COLORS = { pending: 'warning', approved: 'success', rejected: 'error' }
const columns = [
  { field: 'id', headerName: 'ID', width: 70 },
  { field: 'booking', headerName: 'Booking', width: 100 },
  { field: 'guest_name', headerName: 'Guest', width: 180 },
  { field: 'amount', headerName: 'Amount (€)', width: 120, renderCell: (r) => `€${Number(r.amount || 0).toFixed(2)}` },
  { field: 'reason', headerName: 'Reason', width: 200, renderCell: (r) => r.reason?.slice(0, 50) + (r.reason?.length > 50 ? '...' : '') },
  { field: 'status', headerName: 'Status', width: 120, renderCell: (r) => <Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} /> },
  { field: 'created_at', headerName: 'Requested', width: 120, renderCell: (r) => r.created_at ? new Date(r.created_at).toLocaleDateString() : '—' },
]

export default function RefundsListPage() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('')
  const { data, isLoading, error } = useGetRefundsQuery({ status: status || undefined })
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ mb: 2 }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Status</InputLabel>
          <Select value={status} label="Status" onChange={(e) => setStatus(e.target.value)}>
            {['', 'pending', 'approved', 'rejected'].map((s) => <MenuItem key={s} value={s}>{s || 'All'}</MenuItem>)}
          </Select>
        </FormControl>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={(r) => navigate(`/admin/refunds/${r.id}`)} />
    </AppLayout>
  )
}
