import React, { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Box, Button, Paper, TextField, Typography } from '@mui/material'
import { ArrowBack, CheckCircle } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetPaymentQuery, useVerifyPaymentMutation } from '../../features/payments/paymentsApi'

export default function PaymentVerifyPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: payment, isLoading, error } = useGetPaymentQuery(id)
  const [verifyPayment, { isLoading: verifying }] = useVerifyPaymentMutation()

  const [verificationCode, setVerificationCode] = useState('')
  const [feedback, setFeedback] = useState(null)

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!payment) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFeedback(null)

    const result = await verifyPayment({ id, verification_code: verificationCode.trim() })
    if (result.error) {
      setFeedback({ type: 'error', text: result.error?.data?.error || 'Verification failed. Please check the code and try again.' })
      return
    }

    setFeedback({ type: 'success', text: 'Payment verified successfully.' })
    navigate('/payment-success', { replace: true })
  }

  return (
    <AppLayout>
      <Box sx={{ mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate(-1)}>Back</Button>
      </Box>

      <Paper sx={{ p: 3, maxWidth: 560 }}>
        <Typography variant="h5" sx={{ mb: 1 }}>Verify Payment</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Enter the verification code sent to the guest email to complete payment #{payment.id}.
        </Typography>

        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            fullWidth
            required
            label="Verification Code"
            value={verificationCode}
            onChange={(e) => setVerificationCode(e.target.value)}
            inputProps={{ maxLength: 12 }}
            sx={{ mb: 2 }}
          />

          {feedback && (
            <Alert icon={feedback.type === 'success' ? <CheckCircle fontSize="inherit" /> : undefined} severity={feedback.type} sx={{ mb: 2 }}>
              {feedback.text}
            </Alert>
          )}

          <Button type="submit" variant="contained" disabled={verifying || verificationCode.trim().length === 0}>
            {verifying ? 'Verifying...' : 'Verify Payment'}
          </Button>
        </Box>
      </Paper>
    </AppLayout>
  )
}
