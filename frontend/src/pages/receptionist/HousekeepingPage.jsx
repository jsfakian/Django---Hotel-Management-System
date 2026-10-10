import React, { useState } from 'react'
import {
  Box, Button, Chip, FormControl, InputLabel, MenuItem, Select, TextField, Typography,
} from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import DataTable from '../../components/common/DataTable'
import ErrorAlert from '../../components/common/ErrorAlert'
import {
  useGetHousekeepingQuery,
  useUpdateHousekeepingMutation,
} from '../../features/front-desk/frontDeskApi'

const STATUS_OPTIONS = ['available', 'cleaning', 'occupied', 'maintenance', 'blocked']
const STATUS_COLORS = {
  available: 'success',
  cleaning: 'warning',
  occupied: 'primary',
  maintenance: 'error',
  blocked: 'default',
}

export default function HousekeepingPage() {
  const [propertyId, setPropertyId] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const { data, isLoading, error } = useGetHousekeepingQuery({
    property_id: propertyId || undefined,
    status: statusFilter || undefined,
  })
  const [updateHousekeeping, { isLoading: saving }] = useUpdateHousekeepingMutation()

  const rows = data?.results || data?.rooms || data || []

  const setStatus = async (room, status) => {
    await updateHousekeeping({ room_id: room.id, status })
  }

  const columns = [
    { field: 'room_number', headerName: 'Room', width: 100 },
    { field: 'room_type', headerName: 'Type', width: 120, renderCell: (r) => r.room_type || r.room_type_name || '—' },
    { field: 'floor', headerName: 'Floor', width: 80 },
    {
      field: 'status',
      headerName: 'Status',
      width: 130,
      renderCell: (r) => (
        <Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} />
      ),
    },
    {
      field: 'actions',
      headerName: 'Update',
      width: 280,
      renderCell: (r) => (
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {STATUS_OPTIONS.map((s) => (
            <Button
              key={s}
              size="small"
              disabled={saving || r.status === s}
              onClick={(e) => { e.stopPropagation(); setStatus(r, s) }}
            >
              {s}
            </Button>
          ))}
        </Box>
      ),
    },
  ]

  return (
    <AppLayout>
      <Typography variant="h5" sx={{ mb: 1, fontFamily: '"Fraunces", Georgia, serif' }}>Housekeeping</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Room status board for cleaning and turnover.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <TextField size="small" label="Property ID" type="number" value={propertyId} onChange={(e) => setPropertyId(e.target.value)} />
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Status</InputLabel>
          <Select label="Status" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <MenuItem value="">All</MenuItem>
            {STATUS_OPTIONS.map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
          </Select>
        </FormControl>
      </Box>

      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={Array.isArray(rows) ? rows : []} loading={isLoading} />
    </AppLayout>
  )
}
