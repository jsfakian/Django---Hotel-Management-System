import React, { useState } from 'react'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import {
  Box,
  TextField,
  Button,
  Typography,
  Link,
  CircularProgress,
  InputAdornment,
  IconButton,
} from '@mui/material'
import { Visibility, VisibilityOff } from '@mui/icons-material'
import { jwtDecode } from 'jwt-decode'
import { useLoginMutation } from '../../features/auth/authApi'
import { setCredentials } from '../../features/auth/authSlice'
import ErrorAlert from '../../components/common/ErrorAlert'
import AuthShell from '../../components/auth/AuthShell'

const ROLE_DASHBOARDS = {
  admin: '/admin/dashboard',
  manager: '/manager/dashboard',
  receptionist: '/receptionist/dashboard',
  staff: '/staff/dashboard',
  guest: '/guest/dashboard',
}

export default function LoginPage() {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const [login, { isLoading, error }] = useLoginMutation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const result = await login({ username: email, password }).unwrap()
      dispatch(setCredentials(result))

      const decoded = jwtDecode(result.access)
      const role = decoded.role || 'guest'
      navigate(ROLE_DASHBOARDS[role] || '/guest/dashboard', { replace: true })
    } catch {
      // error handled by RTK Query error state
    }
  }

  return (
    <AuthShell title="Welcome back" subtitle="Sign in to manage stays, front desk, or your guest account.">
      {error && <ErrorAlert error={error} />}

      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
        <TextField
          fullWidth
          label="Username or Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          margin="normal"
          required
          autoFocus
          autoComplete="username"
        />
        <TextField
          fullWidth
          label="Password"
          type={showPassword ? 'text' : 'password'}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          margin="normal"
          required
          autoComplete="current-password"
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setShowPassword((v) => !v)}
                  edge="end"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        <Button
          type="submit"
          fullWidth
          variant="contained"
          size="large"
          disabled={isLoading}
          sx={{ mt: 2.5, mb: 1.5 }}
        >
          {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
        </Button>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 1 }}>
          <Link component={RouterLink} to="/forgot-password" variant="body2">
            Forgot password?
          </Link>
          <Typography variant="body2" color="text.secondary">
            Guest?{' '}
            <Link component={RouterLink} to="/register">
              Create an account
            </Link>
          </Typography>
        </Box>
      </Box>
    </AuthShell>
  )
}
