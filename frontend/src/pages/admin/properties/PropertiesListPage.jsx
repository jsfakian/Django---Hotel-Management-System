import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button } from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetPropertiesQuery } from '../../../features/properties/propertiesApi'

const columns = [
  { field: 'name', headerName: 'Name', width: 200 },
  { field: 'city', headerName: 'City', width: 140 },
  { field: 'country', headerName: 'Country', width: 120 },
  { field: 'star_rating', headerName: 'Stars', width: 80 },
  { field: 'rooms_count', headerName: 'Rooms', width: 80 },
  { field: 'phone', headerName: 'Phone', width: 140 },
  { field: 'email', headerName: 'Email', width: 200 },
]

export default function PropertiesListPage() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useGetPropertiesQuery()
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" startIcon={<Add />} onClick={() => navigate('/admin/properties/new')}>Add Property</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={(row) => navigate(`/admin/properties/${row.id}`)} />
    </AppLayout>
  )
}
