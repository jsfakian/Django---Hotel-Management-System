import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, FormControl, InputLabel, Select, MenuItem, Chip } from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetContractsQuery } from '../../../features/contracts/contractsApi'

const STATUS_COLORS = { draft: 'warning', active: 'success', expired: 'default', terminated: 'error' }
const columns = [
  { field: 'id', headerName: 'Contract #', width: 110 },
  { field: 'travel_agency_name', headerName: 'Travel Agency', width: 200 },
  { field: 'property_name', headerName: 'Property', width: 180 },
  { field: 'commission_rate', headerName: 'Commission %', width: 130, renderCell: (r) => `${r.commission_rate || 0}%` },
  { field: 'start_date', headerName: 'Start', width: 110 },
  { field: 'end_date', headerName: 'End', width: 110 },
  { field: 'status', headerName: 'Status', width: 120, renderCell: (r) => <Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} /> },
  { field: 'signed', headerName: 'Signed', width: 80, renderCell: (r) => r.signed ? 'Yes' : 'No' },
]

export default function ContractsListPage() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('')
  const { data, isLoading, error } = useGetContractsQuery({ status: status || undefined })
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Status</InputLabel>
          <Select value={status} label="Status" onChange={(e) => setStatus(e.target.value)}>
            {['', 'draft', 'active', 'expired', 'terminated'].map((s) => <MenuItem key={s} value={s}>{s || 'All'}</MenuItem>)}
          </Select>
        </FormControl>
        <Button variant="contained" startIcon={<Add />} onClick={() => navigate('/admin/contracts/new')}>New Contract</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={(r) => navigate(`/admin/contracts/${r.id}`)} />
    </AppLayout>
  )
}
