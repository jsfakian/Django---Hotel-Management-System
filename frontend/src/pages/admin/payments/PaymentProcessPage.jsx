import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Box, Button, TextField, MenuItem, Select, FormControl, InputLabel, Paper, Typography, Grid } from '@mui/material'
import { Save } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useCreatePaymentMutation } from '../../../features/payments/paymentsApi'

export default function PaymentProcessPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const params = new URLSearchParams(location.search)
  const [createPayment, { isLoading, error }] = useCreatePaymentMutation()
  const [form, setForm] = useState({ booking: params.get('booking') || '', amount: '', payment_method: 'card', notes: '' })

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await createPayment(form)
    if (!result.error) navigate('/admin/payments/success', { state: { paymentId: result.data?.id, amount: form.amount } })
  }

  return (
    <AppLayout>
      <Typography variant="h5" sx={{ mb: 3 }}>Process Payment</Typography>
      {error && <ErrorAlert error={error} />}
      <Paper sx={{ p: 3, maxWidth: 600 }}>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12}><TextField fullWidth required label="Booking ID" name="booking" value={form.booking} onChange={handleChange} /></Grid>
            <Grid item xs={12} sm={6}><TextField fullWidth required type="number" label="Amount (€)" name="amount" value={form.amount} onChange={handleChange} inputProps={{ min: 0, step: '0.01' }} /></Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Payment Method</InputLabel>
                <Select name="payment_method" value={form.payment_method} label="Payment Method" onChange={handleChange}>
                  {['cash', 'card', 'bank_transfer', 'online'].map((m) => <MenuItem key={m} value={m}>{m.replace('_', ' ')}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}><TextField fullWidth multiline rows={3} label="Notes" name="notes" value={form.notes} onChange={handleChange} /></Grid>
          </Grid>
          <Box sx={{ mt: 3 }}>
            <Button type="submit" variant="contained" startIcon={<Save />} disabled={isLoading}>
              {isLoading ? 'Processing...' : 'Process Payment'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </AppLayout>
  )
}
