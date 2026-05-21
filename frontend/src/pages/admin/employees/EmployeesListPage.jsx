import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, FormControl, InputLabel, Select, MenuItem, Chip } from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetEmployeesQuery } from '../../../features/employees/employeesApi'

const STATUS_COLORS = { active: 'success', inactive: 'default', on_leave: 'warning', terminated: 'error' }
const columns = [
  { field: 'full_name', headerName: 'Name', width: 180, renderCell: (r) => `${r.user?.first_name || ''} ${r.user?.last_name || ''}`.trim() || r.id },
  { field: 'position', headerName: 'Position', width: 160 },
  { field: 'department', headerName: 'Department', width: 140 },
  { field: 'property_name', headerName: 'Property', width: 160 },
  { field: 'status', headerName: 'Status', width: 120, renderCell: (r) => <Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} /> },
  { field: 'hire_date', headerName: 'Hired', width: 110 },
  { field: 'salary', headerName: 'Salary (€)', width: 120, renderCell: (r) => `€${Number(r.salary || 0).toFixed(2)}` },
]

export default function EmployeesListPage() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('')
  const { data, isLoading, error } = useGetEmployeesQuery({ status: status || undefined })
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Status</InputLabel>
          <Select value={status} label="Status" onChange={(e) => setStatus(e.target.value)}>
            {['', 'active', 'inactive', 'on_leave', 'terminated'].map((s) => <MenuItem key={s} value={s}>{s || 'All'}</MenuItem>)}
          </Select>
        </FormControl>
        <Button variant="contained" startIcon={<Add />} onClick={() => navigate('/admin/employees/new')}>Add Employee</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={(r) => navigate(`/admin/employees/${r.id}`)} />
    </AppLayout>
  )
}
