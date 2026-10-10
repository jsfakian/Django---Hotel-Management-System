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

function SummaryCard({ gridProps, tint, icon, label, value }) {
  return (
    <Grid item xs={12} {...gridProps}>
      <Card>
        <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              width: 52,
              height: 52,
              borderRadius: 2,
              backgroundColor: `${tint}.light`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {React.cloneElement(icon, { sx: { color: `${tint}.main`, fontSize: 28 } })}
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">{label}</Typography>
            <Typography variant="h4" fontWeight={700}>{value}</Typography>
          </Box>
        </CardContent>
      </Card>
    </Grid>
  )
}

function TaskListItem({ task }) {
  return (
    <ListItem
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
      <Chip label={task.type} size="small" variant="outlined" sx={{ textTransform: 'capitalize' }} />
    </ListItem>
  )
}

function TaskList({ tasks }) {
  return (
    <Grid item xs={12}>
      <Card>
        <CardContent>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            Today&apos;s Task List
          </Typography>
          <List dense>
            {tasks.map((task) => <TaskListItem key={task.id} task={task} />)}
          </List>
        </CardContent>
      </Card>
    </Grid>
  )
}

export default function StaffDashboard() {
  const user = useSelector(selectCurrentUser)

  const pending = PLACEHOLDER_TASKS.filter((t) => !t.done)
  const completed = PLACEHOLDER_TASKS.filter((t) => t.done)
  const maintenance = PLACEHOLDER_TASKS.filter((t) => t.type === 'maintenance')

  return (
    <AppLayout>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5">Staff Dashboard</Typography>
        <Typography variant="body2" color="text.secondary">
          Hello, {user?.username || 'Staff Member'} — here are your tasks for today
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <SummaryCard gridProps={{ sm: 6, md: 4 }} tint="warning" icon={<Assignment />} label="Pending Tasks" value={pending.length} />
        <SummaryCard gridProps={{ sm: 6, md: 4 }} tint="success" icon={<CheckCircleOutline />} label="Completed Today" value={completed.length} />
        <SummaryCard gridProps={{ md: 4 }} tint="primary" icon={<Build />} label="Maintenance" value={maintenance.length} />
        <TaskList tasks={PLACEHOLDER_TASKS} />
      </Grid>
    </AppLayout>
  )
}
