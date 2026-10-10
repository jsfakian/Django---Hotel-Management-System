import React, { useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { Box, TextField, Button, Typography, Link, CircularProgress, Alert } from '@mui/material'
import { useForgotPasswordMutation } from '../../features/auth/authApi'
import ErrorAlert from '../../components/common/ErrorAlert'
import AuthShell from '../../components/auth/AuthShell'

export default function ForgotPasswordPage() {
  const [forgotPassword, { isLoading, error }] = useForgotPasswordMutation()
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await forgotPassword({ email }).unwrap()
      setSubmitted(true)
    } catch {
      // error handled by RTK Query error state
    }
  }

  return (
    <AuthShell
      title="Reset password"
      subtitle="Enter the email on your account and we will send a reset link if it exists."
    >
      {submitted ? (
        <Alert severity="success">
          If that email address is registered, you will receive a password reset link shortly.
          Please check your inbox.
        </Alert>
      ) : (
        <>
          {error && <ErrorAlert error={error} />}
          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
            <TextField
              fullWidth
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              margin="normal"
              required
              autoFocus
              autoComplete="email"
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={isLoading}
              sx={{ mt: 2.5, mb: 1.5 }}
            >
              {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Send Reset Link'}
            </Button>
          </Box>
        </>
      )}

      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        <Link component={RouterLink} to="/login">
          Back to sign in
        </Link>
      </Typography>
    </AuthShell>
  )
}
