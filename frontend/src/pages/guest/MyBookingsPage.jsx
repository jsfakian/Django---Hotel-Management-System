import React from 'react'
import { Box, Typography, Chip } from '@mui/material'
import { useGetBookingsQuery } from '../../features/bookings/bookingsApi'
import DataTable from '../../components/common/DataTable'
import ErrorAlert from '../../components/common/ErrorAlert'
import AppLayout from '../../components/layout/AppLayout'

const STATUS_COLORS = {
  confirmed: 'success',
  pending: 'warning',
  checked_in: 'info',
  checked_out: 'default',
  cancelled: 'error',
}

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB')
}

export default function MyBookingsPage() {
  const { data, isLoading, error } = useGetBookingsQuery({})

  const rows = data?.results ?? (Array.isArray(data) ? data : [])

  const columns = [
    { field: 'id', headerName: 'ID', width: 60 },
    {
      field: 'room',
      headerName: 'Room',
      width: 120,
      renderCell: ({ row }) =>
        row.room_number || row.room?.number || row.room || '—',
    },
    {
      field: 'check_in_date',
      headerName: 'Check-in',
      width: 120,
      renderCell: ({ value }) => formatDate(value),
    },
    {
      field: 'check_out_date',
      headerName: 'Check-out',
      width: 120,
      renderCell: ({ value }) => formatDate(value),
    },
    {
      field: 'total_price',
      headerName: 'Total',
      width: 120,
      renderCell: ({ value }) =>
        value != null ? `€${Number(value).toLocaleString()}` : '—',
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 130,
      renderCell: ({ value }) => (
        <Chip
          label={value?.replace('_', ' ') || '—'}
          size="small"
          color={STATUS_COLORS[value] || 'default'}
          sx={{ textTransform: 'capitalize' }}
        />
      ),
    },
  ]

  return (
    <AppLayout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5">My Bookings</Typography>
        <Typography variant="body2" color="text.secondary">
          Your reservation history
        </Typography>
      </Box>

      {error && <ErrorAlert error={error} title="Failed to load bookings" />}
      <DataTable columns={columns} rows={rows} loading={isLoading} />
    </AppLayout>
  )
}
