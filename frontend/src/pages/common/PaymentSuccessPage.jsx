import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Box, Card, CardContent, Typography, Button } from '@mui/material'
import { CheckCircle } from '@mui/icons-material'

export default function PaymentSuccessPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const { paymentId, amount } = location.state || {}

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default', p: 2 }}>
      <Card sx={{ maxWidth: 440, width: '100%', textAlign: 'center' }}>
        <CardContent sx={{ p: 4 }}>
          <CheckCircle sx={{ fontSize: 72, color: 'success.main', mb: 2 }} />
          <Typography variant="h5" fontWeight={700} gutterBottom>Payment Successful</Typography>
          {paymentId && <Typography color="text.secondary">Payment ID: #{paymentId}</Typography>}
          {amount && <Typography variant="h6" sx={{ mt: 1 }}>€{Number(amount).toFixed(2)}</Typography>}
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 3 }}>
            <Button variant="contained" onClick={() => navigate('/admin/invoices')}>View Invoices</Button>
            <Button variant="outlined" onClick={() => navigate('/admin/bookings')}>Back to Bookings</Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}
