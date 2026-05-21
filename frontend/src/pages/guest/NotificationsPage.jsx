import React from 'react'
import { Box, Button, List, ListItem, ListItemText, ListItemAvatar, Avatar, Typography, Divider, Badge } from '@mui/material'
import { Notifications, Bookmark } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetNotificationsQuery, useMarkReadMutation, useMarkAllReadMutation } from '../../features/notifications/notificationsApi'

export default function NotificationsPage() {
  const { data, isLoading, error } = useGetNotificationsQuery()
  const [markRead] = useMarkReadMutation()
  const [markAllRead, { isLoading: marking }] = useMarkAllReadMutation()
  const notifications = data?.results || data || []
  const unreadCount = notifications.filter((n) => !n.is_read).length

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Badge badgeContent={unreadCount} color="error"><Notifications /></Badge>
        <Button size="small" onClick={() => markAllRead()} disabled={marking || unreadCount === 0}>Mark all read</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <List>
        {notifications.length === 0 && <Typography color="text.secondary">No notifications.</Typography>}
        {notifications.map((n, i) => (
          <React.Fragment key={n.id}>
            <ListItem sx={{ bgcolor: n.is_read ? 'transparent' : 'action.hover', cursor: 'pointer', borderRadius: 1 }} onClick={() => !n.is_read && markRead(n.id)}>
              <ListItemAvatar><Avatar sx={{ bgcolor: n.is_read ? 'grey.300' : 'primary.main' }}><Bookmark /></Avatar></ListItemAvatar>
              <ListItemText primary={<Typography fontWeight={n.is_read ? 400 : 700}>{n.message || n.title}</Typography>} secondary={n.created_at ? new Date(n.created_at).toLocaleString() : ''} />
            </ListItem>
            {i < notifications.length - 1 && <Divider />}
          </React.Fragment>
        ))}
      </List>
    </AppLayout>
  )
}
