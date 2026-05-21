import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, FormControl, InputLabel, Select, MenuItem, Chip, Switch, FormControlLabel } from '@mui/material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetUsersQuery } from '../../../features/users/usersApi'

const ROLES = ['', 'admin', 'manager', 'receptionist', 'staff', 'guest']
const ROLE_COLORS = { admin: 'error', manager: 'warning', receptionist: 'info', staff: 'default', guest: 'success' }

const columns = [
  { field: 'username', headerName: 'Username', width: 160 },
  { field: 'email', headerName: 'Email', width: 220 },
  { field: 'first_name', headerName: 'First Name', width: 140 },
  { field: 'last_name', headerName: 'Last Name', width: 140 },
  { field: 'role', headerName: 'Role', width: 120, renderCell: (row) => row.role ? <Chip size="small" label={row.role} color={ROLE_COLORS[row.role] || 'default'} /> : '—' },
  { field: 'is_active', headerName: 'Active', width: 80, renderCell: (row) => <Chip size="small" label={row.is_active ? 'Yes' : 'No'} color={row.is_active ? 'success' : 'default'} /> },
  { field: 'date_joined', headerName: 'Joined', width: 120, renderCell: (row) => row.date_joined ? new Date(row.date_joined).toLocaleDateString() : '—' },
]

export default function UsersListPage() {
  const navigate = useNavigate()
  const [role, setRole] = useState('')
  const [activeOnly, setActiveOnly] = useState(false)
  const { data, isLoading, error } = useGetUsersQuery({ role: role || undefined, is_active: activeOnly || undefined })
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Role</InputLabel>
          <Select value={role} label="Role" onChange={(e) => setRole(e.target.value)}>
            {ROLES.map((r) => <MenuItem key={r} value={r}>{r || 'All roles'}</MenuItem>)}
          </Select>
        </FormControl>
        <FormControlLabel control={<Switch checked={activeOnly} onChange={(e) => setActiveOnly(e.target.checked)} />} label="Active only" />
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={(row) => navigate(`/admin/users/${row.id}`)} />
    </AppLayout>
  )
}
