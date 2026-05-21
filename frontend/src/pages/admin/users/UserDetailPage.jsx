import React from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Box, Button, Paper, Typography, Grid, Chip, Alert } from '@mui/material'
import { ArrowBack } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetUserQuery, useUpdateUserMutation } from '../../../features/users/usersApi'

export default function UserDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { data: user, isLoading, error } = useGetUserQuery(id)
  const [updateUser, { isLoading: updating, error: updateError, isSuccess }] = useUpdateUserMutation()

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>
  if (error) return <AppLayout><ErrorAlert error={error} /></AppLayout>
  if (!user) return null

  const toggleActive = () => updateUser({ id, is_active: !user.is_active })

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Button startIcon={<ArrowBack />} onClick={() => navigate('/admin/users')}>Back</Button>
      </Box>
      {isSuccess && <Alert severity="success" sx={{ mb: 2 }}>User updated.</Alert>}
      {updateError && <ErrorAlert error={updateError} />}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Typography variant="h5">{user.username}</Typography>
          <Chip label={user.is_active ? 'Active' : 'Inactive'} color={user.is_active ? 'success' : 'default'} />
          {user.role && <Chip label={user.role} color="info" />}
        </Box>
        <Grid container spacing={2} sx={{ mb: 3 }}>
          {[['Email', user.email], ['First Name', user.first_name], ['Last Name', user.last_name], ['Date Joined', user.date_joined ? new Date(user.date_joined).toLocaleDateString() : '—'], ['Last Login', user.last_login ? new Date(user.last_login).toLocaleDateString() : '—']].map(([label, val]) => (
            <Grid item xs={12} sm={6} md={4} key={label}>
              <Typography variant="caption" color="text.secondary">{label}</Typography>
              <Typography variant="body1">{val || '—'}</Typography>
            </Grid>
          ))}
        </Grid>
        <Button variant="outlined" color={user.is_active ? 'error' : 'success'} onClick={toggleActive} disabled={updating}>
          {user.is_active ? 'Deactivate User' : 'Activate User'}
        </Button>
      </Paper>
    </AppLayout>
  )
}
