import React, { useState } from 'react'
import { Box, Button, TextField, Paper, Typography, Grid, Alert } from '@mui/material'
import { Save } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useCreateRefundMutation } from '../../features/refunds/refundsApi'

export default function RefundRequestPage() {
  const [createRefund, { isLoading, error }] = useCreateRefundMutation()
  const [form, setForm] = useState({ booking: '', amount: '', reason: '' })
  const [success, setSuccess] = useState(false)

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await createRefund(form)
    if (!result.error) { setSuccess(true); setForm({ booking: '', amount: '', reason: '' }) }
  }

  return (
    <AppLayout>
      <Typography variant="h5" sx={{ mb: 3 }}>Request a Refund</Typography>
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(false)}>Refund request submitted. We'll review it shortly.</Alert>}
      {error && <ErrorAlert error={error} />}
      <Paper sx={{ p: 3, maxWidth: 600 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12}><TextField fullWidth required label="Booking ID" name="booking" value={form.booking} onChange={handleChange} /></Grid>
            <Grid item xs={12}><TextField fullWidth required type="number" label="Refund Amount (€)" name="amount" value={form.amount} onChange={handleChange} inputProps={{ min: 0, step: '0.01' }} /></Grid>
            <Grid item xs={12}><TextField fullWidth required multiline rows={4} label="Reason for Refund" name="reason" value={form.reason} onChange={handleChange} /></Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Button type="submit" variant="contained" startIcon={<Save />} disabled={isLoading}>
              {isLoading ? 'Submitting...' : 'Submit Refund Request'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </AppLayout>
  )
}
