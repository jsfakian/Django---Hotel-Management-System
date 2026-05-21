import React, { useState } from 'react'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import { Box, Card, CardContent, TextField, Button, Typography, Link, CircularProgress, InputAdornment, IconButton, Alert } from '@mui/material'
import { Visibility, VisibilityOff, Hotel } from '@mui/icons-material'
import axiosInstance from '../../services/axiosInstance'

export default function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', confirm_password: '' })
  const [showPw, setShowPw] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.password !== form.confirm_password) { setError('Passwords do not match.'); return }
    setLoading(true); setError(null)
    try {
      await axiosInstance.post('/auth/register/', { email: form.email, password: form.password, first_name: form.first_name, last_name: form.last_name, role: 'guest' })
      navigate('/login', { state: { registered: true } })
    } catch (err) {
      const data = err.response?.data
      setError(typeof data === 'object' ? Object.values(data).flat().join(' ') : 'Registration failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: 'background.default', p: 2 }}>
      <Card sx={{ width: '100%', maxWidth: 460 }}>
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <Hotel sx={{ fontSize: 48, color: 'primary.main' }} />
            <Typography variant="h5" fontWeight={700} color="primary.main">NEPHELE HMS</Typography>
            <Typography variant="body2" color="text.secondary" mt={0.5}>Create your guest account</Typography>
          </Box>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Box component="form" onSubmit={handleSubmit}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField fullWidth required label="First Name" name="first_name" value={form.first_name} onChange={handleChange} margin="normal" />
              <TextField fullWidth required label="Last Name" name="last_name" value={form.last_name} onChange={handleChange} margin="normal" />
            </Box>
            <TextField fullWidth required label="Email" name="email" type="email" value={form.email} onChange={handleChange} margin="normal" autoComplete="email" />
            <TextField fullWidth required label="Password" name="password" type={showPw ? 'text' : 'password'} value={form.password} onChange={handleChange} margin="normal"
              InputProps={{ endAdornment: <InputAdornment position="end"><IconButton onClick={() => setShowPw(v => !v)} edge="end">{showPw ? <VisibilityOff /> : <Visibility />}</IconButton></InputAdornment> }} />
            <TextField fullWidth required label="Confirm Password" name="confirm_password" type="password" value={form.confirm_password} onChange={handleChange} margin="normal" />
            <Button type="submit" fullWidth variant="contained" size="large" disabled={loading} sx={{ mt: 2, mb: 1 }}>
              {loading ? <CircularProgress size={24} color="inherit" /> : 'Create Account'}
            </Button>
            <Box sx={{ textAlign: 'center', mt: 1 }}>
              <Link component={RouterLink} to="/login" variant="body2">Already have an account? Sign in</Link>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}
