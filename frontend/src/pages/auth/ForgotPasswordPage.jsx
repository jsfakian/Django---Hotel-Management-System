import React, { useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Link,
  CircularProgress,
  Alert,
} from '@mui/material'
import { Hotel } from '@mui/icons-material'
import { useForgotPasswordMutation } from '../../features/auth/authApi'
import ErrorAlert from '../../components/common/ErrorAlert'

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
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'background.default',
        p: 2,
      }}
    >
      <Card sx={{ width: '100%', maxWidth: 420 }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <Hotel sx={{ fontSize: 48, color: 'primary.main' }} />
            <Typography variant="h5" fontWeight={700} color="primary.main">
              Reset Password
            </Typography>
            <Typography variant="body2" color="text.secondary" mt={0.5}>
              Enter your email to receive a reset link
            </Typography>
          </Box>

          {submitted ? (
            <Alert severity="success">
              If that email address is registered, you will receive a password reset link shortly.
              Please check your inbox.
            </Alert>
          ) : (
            <>
              {error && <ErrorAlert error={error} />}
              <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
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
                  sx={{ mt: 2, mb: 1 }}
                >
                  {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Send Reset Link'}
                </Button>
              </Box>
            </>
          )}

          <Box sx={{ textAlign: 'center', mt: 2 }}>
            <Link component={RouterLink} to="/login" variant="body2">
              Back to sign in
            </Link>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}
