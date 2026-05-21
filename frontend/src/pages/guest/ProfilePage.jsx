import React, { useState } from 'react'
import { Box, Paper, Typography, Grid, TextField, Button, Alert, Divider } from '@mui/material'
import { Save, Lock } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import { useSelector } from 'react-redux'
import { selectCurrentUser } from '../../features/auth/authSlice'
import axiosInstance from '../../services/axiosInstance'

export default function ProfilePage() {
  const user = useSelector(selectCurrentUser)
  const [pwForm, setPwForm] = useState({ old_password: '', new_password: '', confirm_password: '' })
  const [pwLoading, setPwLoading] = useState(false)
  const [pwMsg, setPwMsg] = useState(null)

  const handlePwChange = (e) => setPwForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handlePwSubmit = async (e) => {
    e.preventDefault()
    if (pwForm.new_password !== pwForm.confirm_password) { setPwMsg({ type: 'error', text: 'Passwords do not match.' }); return }
    setPwLoading(true)
    try {
      await axiosInstance.post('/auth/change-password/', { old_password: pwForm.old_password, new_password: pwForm.new_password })
      setPwMsg({ type: 'success', text: 'Password changed successfully.' })
      setPwForm({ old_password: '', new_password: '', confirm_password: '' })
    } catch {
      setPwMsg({ type: 'error', text: 'Failed to change password. Check your current password.' })
    } finally {
      setPwLoading(false)
    }
  }

  return (
    <AppLayout>
      <Typography variant="h5" sx={{ mb: 3 }}>My Profile</Typography>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Account Information</Typography>
        <Grid container spacing={2}>
          {[['Username', user?.username], ['Email', user?.email], ['Role', user?.role]].map(([label, val]) => (
            <Grid item xs={12} sm={4} key={label}>
              <Typography variant="caption" color="text.secondary">{label}</Typography>
              <Typography>{val || '—'}</Typography>
            </Grid>
          ))}
        </Grid>
      </Paper>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Lock color="primary" />
          <Typography variant="h6">Change Password</Typography>
        </Box>
        <Divider sx={{ mb: 2 }} />
        {pwMsg && <Alert severity={pwMsg.type} sx={{ mb: 2 }} onClose={() => setPwMsg(null)}>{pwMsg.text}</Alert>}
        <Box component="form" onSubmit={handlePwSubmit} sx={{ maxWidth: 400 }}>
          <TextField fullWidth required label="Current Password" name="old_password" type="password" value={pwForm.old_password} onChange={handlePwChange} margin="normal" />
          <TextField fullWidth required label="New Password" name="new_password" type="password" value={pwForm.new_password} onChange={handlePwChange} margin="normal" />
          <TextField fullWidth required label="Confirm New Password" name="confirm_password" type="password" value={pwForm.confirm_password} onChange={handlePwChange} margin="normal" />
          <Button type="submit" variant="contained" startIcon={<Save />} disabled={pwLoading} sx={{ mt: 2 }}>
            {pwLoading ? 'Saving...' : 'Change Password'}
          </Button>
        </Box>
      </Paper>
    </AppLayout>
  )
}
