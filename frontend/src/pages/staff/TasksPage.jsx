import React from 'react'
import { Box, Button, Chip, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import DataTable from '../../components/common/DataTable'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetTasksQuery, useCompleteTaskMutation } from '../../features/tasks/tasksApi'

const PRIORITY_COLORS = { high: 'error', medium: 'warning', low: 'success' }
const STATUS_COLORS = { pending: 'warning', in_progress: 'info', completed: 'success' }

export default function TasksPage() {
  const [targetTask, setTargetTask] = React.useState(null)
  const { data, isLoading, error } = useGetTasksQuery({ assigned_to_me: true })
  const [completeTask] = useCompleteTaskMutation()
  const rows = data?.results || data || []

  const columns = [
    { field: 'title', headerName: 'Task', width: 240 },
    { field: 'priority', headerName: 'Priority', width: 110, renderCell: (r) => <Chip size="small" label={r.priority} color={PRIORITY_COLORS[r.priority] || 'default'} /> },
    { field: 'status', headerName: 'Status', width: 120, renderCell: (r) => <Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} /> },
    { field: 'due_date', headerName: 'Due', width: 120 },
    {
      field: 'actions',
      headerName: '',
      width: 160,
      renderCell: (r) => r.status !== 'completed'
        ? <Button size="small" variant="outlined" onClick={(e) => { e.stopPropagation(); setTargetTask(r) }}>Complete Task</Button>
        : null,
    },
  ]

  return (
    <AppLayout>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} />
      <Dialog open={Boolean(targetTask)} onClose={() => setTargetTask(null)}>
        <DialogTitle>Mark task as completed?</DialogTitle>
        <DialogContent>{targetTask?.title || 'This task'} will be moved to completed.</DialogContent>
        <DialogActions>
          <Button onClick={() => setTargetTask(null)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={async () => {
              await completeTask(targetTask.id)
              setTargetTask(null)
            }}
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
