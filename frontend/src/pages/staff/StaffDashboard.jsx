import React from 'react'
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
} from '@mui/material'
import {
  Assignment,
  Build,
  CheckCircleOutline,
  RadioButtonUnchecked,
} from '@mui/icons-material'
import { useSelector } from 'react-redux'
import { selectCurrentUser } from '../../features/auth/authSlice'
import AppLayout from '../../components/layout/AppLayout'

// Placeholder tasks — in a real implementation these would come from a tasks API
const PLACEHOLDER_TASKS = [
  { id: 1, label: 'Clean Room 101', done: true, type: 'cleaning' },
  { id: 2, label: 'Restock minibar Room 203', done: false, type: 'restocking' },
  { id: 3, label: 'Maintenance check corridor B', done: false, type: 'maintenance' },
  { id: 4, label: 'Laundry pickup Floor 3', done: true, type: 'laundry' },
]

export default function StaffDashboard() {
  const user = useSelector(selectCurrentUser)

  const pending = PLACEHOLDER_TASKS.filter((t) => !t.done)
  const completed = PLACEHOLDER_TASKS.filter((t) => t.done)

  return (
    <AppLayout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5">Staff Dashboard</Typography>
        <Typography variant="body2" color="text.secondary">
          Hello, {user?.username || 'Staff Member'} — here are your tasks for today
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Summary cards */}
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box
                sx={{
                  width: 52,
                  height: 52,
                  borderRadius: 2,
                  backgroundColor: 'warning.light',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Assignment sx={{ color: 'warning.main', fontSize: 28 }} />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Pending Tasks</Typography>
                <Typography variant="h4" fontWeight={700}>{pending.length}</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box
                sx={{
                  width: 52,
                  height: 52,
                  borderRadius: 2,
                  backgroundColor: 'success.light',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <CheckCircleOutline sx={{ color: 'success.main', fontSize: 28 }} />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Completed Today</Typography>
                <Typography variant="h4" fontWeight={700}>{completed.length}</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box
                sx={{
                  width: 52,
                  height: 52,
                  borderRadius: 2,
                  backgroundColor: 'primary.light',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Build sx={{ color: 'primary.main', fontSize: 28 }} />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">Maintenance</Typography>
                <Typography variant="h4" fontWeight={700}>
                  {PLACEHOLDER_TASKS.filter((t) => t.type === 'maintenance').length}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Task list */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                Today's Task List
              </Typography>
              <List dense>
                {PLACEHOLDER_TASKS.map((task) => (
                  <ListItem
                    key={task.id}
                    sx={{
                      borderRadius: 1,
                      mb: 0.5,
                      backgroundColor: task.done ? 'action.hover' : 'background.paper',
                    }}
                  >
                    <ListItemIcon>
                      {task.done ? (
                        <CheckCircleOutline color="success" />
                      ) : (
                        <RadioButtonUnchecked color="action" />
                      )}
                    </ListItemIcon>
                    <ListItemText
                      primary={task.label}
                      sx={{ textDecoration: task.done ? 'line-through' : 'none' }}
                    />
                    <Chip
                      label={task.type}
                      size="small"
                      variant="outlined"
                      sx={{ textTransform: 'capitalize' }}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </AppLayout>
  )
}
