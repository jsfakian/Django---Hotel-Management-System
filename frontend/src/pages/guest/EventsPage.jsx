import React, { useState } from 'react'
import { Box, Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Grid, Alert } from '@mui/material'
import { EventNote } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import DataTable from '../../components/common/DataTable'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetEventsQuery, useAttendEventMutation } from '../../features/events/eventsApi'

const columns = [
  { field: 'title', headerName: 'Event', width: 220 },
  { field: 'date', headerName: 'Date', width: 120 },
  { field: 'time', headerName: 'Time', width: 100 },
  { field: 'location', headerName: 'Location', width: 180 },
  { field: 'capacity', headerName: 'Capacity', width: 100 },
]

export default function EventsPage() {
  const [selected, setSelected] = useState(null)
  const [attendMsg, setAttendMsg] = useState('')
  const { data, isLoading, error } = useGetEventsQuery()
  const [attendEvent, { isLoading: attending }] = useAttendEventMutation()
  const rows = data?.results || data || []

  const handleAttend = async () => {
    const result = await attendEvent(selected.id)
    if (!result.error) { setAttendMsg('You are registered for this event!'); setSelected(null) }
  }

  return (
    <AppLayout>
      {attendMsg && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setAttendMsg('')}>{attendMsg}</Alert>}
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={setSelected} />
      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} maxWidth="sm" fullWidth>
        {selected && (
          <>
            <DialogTitle><EventNote sx={{ mr: 1, verticalAlign: 'middle' }} />{selected.title}</DialogTitle>
            <DialogContent>
              <Grid container spacing={2} sx={{ mt: 0 }}>
                {[['Date', selected.date], ['Time', selected.time], ['Location', selected.location], ['Capacity', selected.capacity]].map(([label, val]) => (
                  <Grid item xs={6} key={label}><Typography variant="caption" color="text.secondary">{label}</Typography><Typography>{val || '—'}</Typography></Grid>
                ))}
                {selected.description && <Grid item xs={12}><Typography variant="caption" color="text.secondary">Description</Typography><Typography variant="body2">{selected.description}</Typography></Grid>}
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelected(null)}>Close</Button>
              <Button variant="contained" onClick={handleAttend} disabled={attending}>Attend</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </AppLayout>
  )
}
