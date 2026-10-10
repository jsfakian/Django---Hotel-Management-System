import React, { useState } from 'react'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import {
  Box,
  TextField,
  Button,
  Typography,
  Link,
  CircularProgress,
  InputAdornment,
  IconButton,
  Alert,
} from '@mui/material'
import { Visibility, VisibilityOff } from '@mui/icons-material'
import axiosInstance from '../../services/axiosInstance'
import AuthShell from '../../components/auth/AuthShell'

function PasswordField({ value, onChange }) {
  const [showPw, setShowPw] = useState(false)
  return (
    <TextField
      fullWidth
      required
      label="Password"
      name="password"
      type={showPw ? 'text' : 'password'}
      value={value}
      onChange={onChange}
      margin="normal"
      InputProps={{
        endAdornment: (
          <InputAdornment position="end">
            <IconButton
              onClick={() => setShowPw((v) => !v)}
              edge="end"
              aria-label={showPw ? 'Hide password' : 'Show password'}
            >
              {showPw ? <VisibilityOff /> : <Visibility />}
            </IconButton>
          </InputAdornment>
        ),
      }}
    />
  )
}

export default function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm_password: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm_password) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      await axiosInstance.post('/auth/register/', {
        email: form.email,
        password: form.password,
        first_name: form.first_name,
        last_name: form.last_name,
        role: 'guest',
      })
      navigate('/login', { state: { registered: true } })
    } catch (err) {
      const data = err.response?.data
      setError(
        typeof data === 'object' ? Object.values(data).flat().join(' ') : 'Registration failed.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell title="Join as a guest" subtitle="Create an account to view stays, invoices, and hotel services.">
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <Box component="form" onSubmit={handleSubmit}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField fullWidth required label="First Name" name="first_name" value={form.first_name} onChange={handleChange} margin="normal" />
          <TextField fullWidth required label="Last Name" name="last_name" value={form.last_name} onChange={handleChange} margin="normal" />
        </Box>
        <TextField
          fullWidth
          required
          label="Email"
          name="email"
          type="email"
          value={form.email}
          onChange={handleChange}
          margin="normal"
          autoComplete="email"
        />
        <PasswordField value={form.password} onChange={handleChange} />
        <TextField
          fullWidth
          required
          label="Confirm Password"
          name="confirm_password"
          type="password"
          value={form.confirm_password}
          onChange={handleChange}
          margin="normal"
        />
        <Button
          type="submit"
          fullWidth
          variant="contained"
          size="large"
          disabled={loading}
          sx={{ mt: 2.5, mb: 1.5 }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : 'Create Account'}
        </Button>
        <Typography variant="body2" color="text.secondary">
          Already have an account?{' '}
          <Link component={RouterLink} to="/login">
            Sign in
          </Link>
        </Typography>
      </Box>
    </AuthShell>
  )
}
