import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, TextField } from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetGuestsQuery } from '../../../features/guests/guestsApi'

const columns = [
  { field: 'first_name', headerName: 'First Name', width: 140 },
  { field: 'last_name', headerName: 'Last Name', width: 140 },
  { field: 'email', headerName: 'Email', width: 220 },
  { field: 'phone', headerName: 'Phone', width: 140 },
  { field: 'nationality', headerName: 'Nationality', width: 120 },
  { field: 'total_bookings', headerName: 'Bookings', width: 100 },
  { field: 'total_nights_stayed', headerName: 'Nights', width: 80 },
]

export default function GuestsListPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const { data, isLoading, error } = useGetGuestsQuery({ search: search || undefined })
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <TextField size="small" label="Search by name or email" value={search} onChange={(e) => setSearch(e.target.value)} sx={{ width: 280 }} />
        <Button variant="contained" startIcon={<Add />} onClick={() => navigate('/admin/guests/new')}>Add Guest</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={(row) => navigate(`/admin/guests/${row.id}`)} />
    </AppLayout>
  )
}
