import React, { useState } from 'react'
import {
  Box,
  Typography,
  Button,
  Chip,
  Stack,
} from '@mui/material'
import {
  useGetBookingsQuery,
  useCheckInMutation,
  useCheckOutMutation,
} from '../../features/bookings/bookingsApi'
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

export default function BookingsPage() {
  const [page, setPage] = useState(1)
  const { data, isLoading, error } = useGetBookingsQuery({ page })
  const [checkIn, { isLoading: checkingIn }] = useCheckInMutation()
  const [checkOut, { isLoading: checkingOut }] = useCheckOutMutation()

  const rows = data?.results ?? (Array.isArray(data) ? data : [])

  const columns = [
    { field: 'id', headerName: 'ID', width: 60 },
    {
      field: 'guest',
      headerName: 'Guest',
      width: 160,
      renderCell: ({ row }) =>
        row.guest_name || row.guest?.full_name || row.guest?.username || row.guest || '—',
    },
    {
      field: 'room',
      headerName: 'Room',
      width: 100,
      renderCell: ({ row }) =>
        row.room_number || row.room?.number || row.room || '—',
    },
    {
      field: 'check_in_date',
      headerName: 'Check-in',
      width: 110,
      renderCell: ({ value }) => formatDate(value),
    },
    {
      field: 'check_out_date',
      headerName: 'Check-out',
      width: 110,
      renderCell: ({ value }) => formatDate(value),
    },
    {
      field: 'status',
      headerName: 'Status',
      width: 120,
      renderCell: ({ value }) => (
        <Chip
          label={value?.replace('_', ' ') || '—'}
          size="small"
          color={STATUS_COLORS[value] || 'default'}
          sx={{ textTransform: 'capitalize' }}
        />
      ),
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 200,
      renderCell: ({ row }) => (
        <Stack direction="row" spacing={1}>
          {row.status === 'confirmed' && (
            <Button
              size="small"
              variant="contained"
              color="success"
              disabled={checkingIn}
              onClick={(e) => {
                e.stopPropagation()
                checkIn(row.id)
              }}
            >
              Check In
            </Button>
          )}
          {row.status === 'checked_in' && (
            <Button
              size="small"
              variant="contained"
              color="warning"
              disabled={checkingOut}
              onClick={(e) => {
                e.stopPropagation()
                checkOut(row.id)
              }}
            >
              Check Out
            </Button>
          )}
        </Stack>
      ),
    },
  ]

  return (
    <AppLayout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5">Bookings</Typography>
        <Typography variant="body2" color="text.secondary">
          Manage reservations, check-ins, and check-outs
        </Typography>
      </Box>

      {error && <ErrorAlert error={error} title="Failed to load bookings" />}

      <DataTable columns={columns} rows={rows} loading={isLoading} />
    </AppLayout>
  )
}
