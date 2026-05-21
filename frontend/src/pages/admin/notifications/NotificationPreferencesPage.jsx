import React, { useEffect, useState } from 'react'
import { Box, Button, Paper, Typography, List, ListItem, ListItemText, Switch, Alert } from '@mui/material'
import AppLayout from '../../../components/layout/AppLayout'
import LoadingSpinner from '../../../components/common/LoadingSpinner'
import { useGetNotificationPreferencesQuery, useUpdateNotificationPreferencesMutation } from '../../../features/notifications/notificationsApi'

const PREF_LABELS = {
  booking_confirmations: 'Booking Confirmations',
  payment_alerts: 'Payment Alerts',
  maintenance_updates: 'Maintenance Updates',
  marketing_emails: 'Marketing Emails',
  system_notifications: 'System Notifications',
}

export default function NotificationPreferencesPage() {
  const { data, isLoading } = useGetNotificationPreferencesQuery()
  const [updatePrefs, { isLoading: saving, isSuccess }] = useUpdateNotificationPreferencesMutation()
  const [prefs, setPrefs] = useState({})

  useEffect(() => { if (data) setPrefs(data) }, [data])

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>

  const handleSave = () => updatePrefs(prefs)

  return (
    <AppLayout>
      <Typography variant="h5" sx={{ mb: 3 }}>Notification Preferences</Typography>
      {isSuccess && <Alert severity="success" sx={{ mb: 2 }}>Preferences saved.</Alert>}
      <Paper sx={{ p: 2, maxWidth: 500 }}>
        <List>
          {Object.entries(PREF_LABELS).map(([key, label]) => (
            <ListItem key={key}>
              <ListItemText primary={label} />
              <Switch checked={Boolean(prefs[key])} onChange={(e) => setPrefs((p) => ({ ...p, [key]: e.target.checked }))} />
            </ListItem>
          ))}
        </List>
        <Box sx={{ mt: 2, px: 2 }}>
          <Button variant="contained" onClick={handleSave} disabled={saving}>Save Preferences</Button>
        </Box>
      </Paper>
    </AppLayout>
  )
}
