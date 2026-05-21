import React from 'react'
import { Box, Typography } from '@mui/material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetTravelAgenciesQuery } from '../../../features/properties/propertiesApi'

const columns = [
  { field: 'name', headerName: 'Agency Name', width: 200 },
  { field: 'contact_person', headerName: 'Contact', width: 160 },
  { field: 'email', headerName: 'Email', width: 200 },
  { field: 'phone', headerName: 'Phone', width: 140 },
  { field: 'commission_rate', headerName: 'Commission %', width: 130, renderCell: (row) => `${row.commission_rate || 0}%` },
  { field: 'is_active', headerName: 'Active', width: 80, renderCell: (row) => (row.is_active ? 'Yes' : 'No') },
]

export default function TravelAgenciesListPage() {
  const { data, isLoading, error } = useGetTravelAgenciesQuery()
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Typography variant="h5" sx={{ mb: 2 }}>Travel Agencies</Typography>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} />
    </AppLayout>
  )
}
