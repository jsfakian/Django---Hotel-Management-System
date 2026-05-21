import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, MenuItem, Select, FormControl, InputLabel, TextField } from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetRoomsQuery } from '../../../features/rooms/roomsApi'

const ROOM_TYPES = ['', 'standard', 'deluxe', 'suite', 'penthouse']
const STATUSES = ['', 'available', 'occupied', 'maintenance', 'cleaning', 'blocked']

const columns = [
  { field: 'room_number', headerName: 'Room #', width: 100 },
  { field: 'room_type', headerName: 'Type', width: 120 },
  { field: 'capacity', headerName: 'Capacity', width: 100 },
  { field: 'beds', headerName: 'Beds', width: 80 },
  { field: 'price_per_night', headerName: 'Price/Night (€)', width: 140, renderCell: (row) => `€${Number(row.price_per_night || 0).toFixed(2)}` },
  { field: 'status', headerName: 'Status', width: 120 },
  { field: 'property_name', headerName: 'Property', width: 160 },
]

export default function RoomsListPage() {
  const navigate = useNavigate()
  const [roomType, setRoomType] = useState('')
  const [status, setStatus] = useState('')
  const { data, isLoading, error } = useGetRoomsQuery({ room_type: roomType || undefined, status: status || undefined })

  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Room Type</InputLabel>
            <Select value={roomType} label="Room Type" onChange={(e) => setRoomType(e.target.value)}>
              {ROOM_TYPES.map((t) => <MenuItem key={t} value={t}>{t || 'All'}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Status</InputLabel>
            <Select value={status} label="Status" onChange={(e) => setStatus(e.target.value)}>
              {STATUSES.map((s) => <MenuItem key={s} value={s}>{s || 'All'}</MenuItem>)}
            </Select>
          </FormControl>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => navigate('/admin/rooms/new')}>
          Add Room
        </Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={(row) => navigate(`/admin/rooms/${row.id}`)} />
    </AppLayout>
  )
}
