import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, TextField } from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetEventsQuery } from '../../../features/events/eventsApi'

const columns = [
  { field: 'title', headerName: 'Title', width: 220 },
  { field: 'date', headerName: 'Date', width: 120 },
  { field: 'time', headerName: 'Time', width: 100 },
  { field: 'location', headerName: 'Location', width: 180 },
  { field: 'capacity', headerName: 'Capacity', width: 100 },
  { field: 'attendees_count', headerName: 'Registered', width: 110 },
]

export default function EventsListPage() {
  const navigate = useNavigate()
  const [dateAfter, setDateAfter] = useState('')
  const [dateBefore, setDateBefore] = useState('')
  const { data, isLoading, error } = useGetEventsQuery({ date_after: dateAfter || undefined, date_before: dateBefore || undefined })
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField size="small" label="From" type="date" InputLabelProps={{ shrink: true }} value={dateAfter} onChange={(e) => setDateAfter(e.target.value)} />
          <TextField size="small" label="To" type="date" InputLabelProps={{ shrink: true }} value={dateBefore} onChange={(e) => setDateBefore(e.target.value)} />
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => navigate('/admin/events/new')}>Create Event</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={(r) => navigate(`/admin/events/${r.id}`)} />
    </AppLayout>
  )
}
