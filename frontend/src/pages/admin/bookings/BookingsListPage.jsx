import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, TextField, MenuItem, Select, FormControl, InputLabel, Chip } from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetBookingsQuery } from '../../../features/bookings/bookingsApi'

const STATUS_COLORS = { pending: 'warning', confirmed: 'info', checked_in: 'success', checked_out: 'default', cancelled: 'error' }

const columns = [
  { field: 'id', headerName: 'ID', width: 60 },
  { field: 'guest_name', headerName: 'Guest', width: 180 },
  { field: 'room_number', headerName: 'Room', width: 100 },
  { field: 'check_in_date', headerName: 'Check-in', width: 120 },
  { field: 'check_out_date', headerName: 'Check-out', width: 120 },
  { field: 'status', headerName: 'Status', width: 130, renderCell: (row) => <Chip size="small" label={row.status} color={STATUS_COLORS[row.status] || 'default'} /> },
  { field: 'total_price', headerName: 'Total (€)', width: 110, renderCell: (row) => `€${Number(row.total_price || 0).toFixed(2)}` },
]

export default function BookingsListPage() {
  const navigate = useNavigate()
  const [status, setStatus] = useState('')
  const [search, setSearch] = useState('')
  const [checkInAfter, setCheckInAfter] = useState('')
  const [checkInBefore, setCheckInBefore] = useState('')

  const { data, isLoading, error } = useGetBookingsQuery({ status: status || undefined, search: search || undefined, check_in_after: checkInAfter || undefined, check_in_before: checkInBefore || undefined })
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField size="small" label="Search guest" value={search} onChange={(e) => setSearch(e.target.value)} />
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Status</InputLabel>
            <Select value={status} label="Status" onChange={(e) => setStatus(e.target.value)}>
              {['', 'pending', 'confirmed', 'checked_in', 'checked_out', 'cancelled'].map((s) => <MenuItem key={s} value={s}>{s || 'All'}</MenuItem>)}
            </Select>
          </FormControl>
          <TextField size="small" label="Check-in after" type="date" InputLabelProps={{ shrink: true }} value={checkInAfter} onChange={(e) => setCheckInAfter(e.target.value)} />
          <TextField size="small" label="Check-in before" type="date" InputLabelProps={{ shrink: true }} value={checkInBefore} onChange={(e) => setCheckInBefore(e.target.value)} />
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => navigate('/admin/bookings/new')}>New Booking</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={(row) => navigate(`/admin/bookings/${row.id}`)} />
    </AppLayout>
  )
}
