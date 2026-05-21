import React, { useState } from 'react'
import { Box, TextField, Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Grid } from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import DataTable from '../../components/common/DataTable'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetGuestsQuery } from '../../features/guests/guestsApi'

const columns = [
  { field: 'first_name', headerName: 'First Name', width: 140 },
  { field: 'last_name', headerName: 'Last Name', width: 140 },
  { field: 'email', headerName: 'Email', width: 220 },
  { field: 'phone', headerName: 'Phone', width: 140 },
  { field: 'nationality', headerName: 'Nationality', width: 120 },
]

export default function GuestsPage() {
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)
  const { data, isLoading, error } = useGetGuestsQuery({ search: search || undefined })
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ mb: 2 }}>
        <TextField size="small" label="Search by name or email" value={search} onChange={(e) => setSearch(e.target.value)} sx={{ width: 280 }} />
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={setSelected} />
      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} maxWidth="sm" fullWidth>
        {selected && (
          <>
            <DialogTitle>{selected.first_name} {selected.last_name}</DialogTitle>
            <DialogContent>
              <Grid container spacing={2} sx={{ mt: 0 }}>
                {[['Email', selected.email], ['Phone', selected.phone], ['Address', selected.address], ['Nationality', selected.nationality], ['Country', selected.country]].map(([label, val]) => (
                  <Grid item xs={12} sm={6} key={label}>
                    <Typography variant="caption" color="text.secondary">{label}</Typography>
                    <Typography>{val || '—'}</Typography>
                  </Grid>
                ))}
              </Grid>
            </DialogContent>
            <DialogActions><Button onClick={() => setSelected(null)}>Close</Button></DialogActions>
          </>
        )}
      </Dialog>
    </AppLayout>
  )
}
