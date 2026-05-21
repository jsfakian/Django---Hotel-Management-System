import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, Dialog, DialogTitle, DialogContent, DialogActions, Typography, Grid, Chip } from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import DataTable from '../../components/common/DataTable'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetPaymentsQuery } from '../../features/payments/paymentsApi'

const STATUS_COLORS = { pending: 'warning', completed: 'success', failed: 'error', refunded: 'info' }
const columns = [
  { field: 'id', headerName: 'ID', width: 70 },
  { field: 'booking', headerName: 'Booking', width: 100 },
  { field: 'guest_name', headerName: 'Guest', width: 180 },
  { field: 'amount', headerName: 'Amount (€)', width: 120, renderCell: (r) => `€${Number(r.amount || 0).toFixed(2)}` },
  { field: 'payment_method', headerName: 'Method', width: 120 },
  { field: 'status', headerName: 'Status', width: 130, renderCell: (r) => <Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} /> },
]

export default function PaymentsPage() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState(null)
  const { data, isLoading, error } = useGetPaymentsQuery()
  const rows = data?.results || data || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" startIcon={<Add />} onClick={() => navigate('/receptionist/payments/process')}>Process Payment</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} onRowClick={setSelected} />
      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} maxWidth="sm" fullWidth>
        {selected && (
          <>
            <DialogTitle>Payment #{selected.id}</DialogTitle>
            <DialogContent>
              <Grid container spacing={2} sx={{ mt: 0 }}>
                {[['Guest', selected.guest_name], ['Booking', selected.booking], ['Amount', `€${Number(selected.amount || 0).toFixed(2)}`], ['Method', selected.payment_method], ['Status', selected.status]].map(([label, val]) => (
                  <Grid item xs={6} key={label}><Typography variant="caption" color="text.secondary">{label}</Typography><Typography>{val}</Typography></Grid>
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
