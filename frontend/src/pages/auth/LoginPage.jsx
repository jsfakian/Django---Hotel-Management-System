import React, { useState } from 'react'
import { useNavigate, Link as RouterLink } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Link,
  CircularProgress,
  InputAdornment,
  IconButton,
} from '@mui/material'
import { Visibility, VisibilityOff, Hotel } from '@mui/icons-material'
import { jwtDecode } from 'jwt-decode'
import { useLoginMutation } from '../../features/auth/authApi'
import { setCredentials } from '../../features/auth/authSlice'
import ErrorAlert from '../../components/common/ErrorAlert'

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
          {/* Logo / branding */}
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <Hotel sx={{ fontSize: 48, color: 'primary.main' }} />
            <Typography variant="h5" fontWeight={700} color="primary.main">
              NEPHELE HMS
            </Typography>
            <Typography variant="body2" color="text.secondary" mt={0.5}>
              Sign in to your account
            </Typography>
          </Box>

          {error && <ErrorAlert error={error} />}

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
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
                    <IconButton onClick={() => setShowPassword((v) => !v)} edge="end">
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
              sx={{ mt: 2, mb: 1 }}
            >
              {isLoading ? <CircularProgress size={24} color="inherit" /> : 'Sign In'}
            </Button>

            <Box sx={{ textAlign: 'center', mt: 1 }}>
              <Link component={RouterLink} to="/forgot-password" variant="body2">
                Forgot password?
              </Link>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  )
}
