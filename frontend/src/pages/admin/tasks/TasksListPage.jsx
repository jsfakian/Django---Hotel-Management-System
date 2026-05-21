import React, { useState } from 'react'
import { Box, Button, Chip, FormControl, InputLabel, Select, MenuItem, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Grid } from '@mui/material'
import { Add } from '@mui/icons-material'
import AppLayout from '../../../components/layout/AppLayout'
import DataTable from '../../../components/common/DataTable'
import ErrorAlert from '../../../components/common/ErrorAlert'
import { useGetTasksQuery, useCreateTaskMutation, useCompleteTaskMutation } from '../../../features/tasks/tasksApi'

const PRIORITY_COLORS = { high: 'error', medium: 'warning', low: 'success' }
const STATUS_COLORS = { pending: 'warning', in_progress: 'info', completed: 'success' }

export default function TasksListPage() {
  const [status, setStatus] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [completeTarget, setCompleteTarget] = useState(null)
  const [form, setForm] = useState({ title: '', description: '', priority: 'medium', due_date: '' })
  const { data, isLoading, error } = useGetTasksQuery({ status: status || undefined })
  const [createTask, { isLoading: creating }] = useCreateTaskMutation()
  const [completeTask] = useCompleteTaskMutation()
  const rows = data?.results || data || []

  const handleCreate = async (e) => {
    e.preventDefault()
    const result = await createTask(form)
    if (!result.error) { setCreateOpen(false); setForm({ title: '', description: '', priority: 'medium', due_date: '' }) }
  }

  const columns = [
    { field: 'title', headerName: 'Task', width: 220 },
    { field: 'assigned_to_name', headerName: 'Assigned To', width: 160 },
    { field: 'priority', headerName: 'Priority', width: 110, renderCell: (r) => <Chip size="small" label={r.priority} color={PRIORITY_COLORS[r.priority] || 'default'} /> },
    { field: 'status', headerName: 'Status', width: 120, renderCell: (r) => <Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} /> },
    { field: 'due_date', headerName: 'Due', width: 120 },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      renderCell: (r) => r.status !== 'completed'
        ? <Button size="small" onClick={(e) => { e.stopPropagation(); setCompleteTarget(r) }}>Complete</Button>
        : null,
    },
  ]

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <FormControl size="small" sx={{ minWidth: 160 }}>
          <InputLabel>Status</InputLabel>
          <Select value={status} label="Status" onChange={(e) => setStatus(e.target.value)}>
            {['', 'pending', 'in_progress', 'completed'].map((s) => <MenuItem key={s} value={s}>{s || 'All'}</MenuItem>)}
          </Select>
        </FormControl>
        <Button variant="contained" startIcon={<Add />} onClick={() => setCreateOpen(true)}>Create Task</Button>
      </Box>
      {error && <ErrorAlert error={error} />}
      <DataTable columns={columns} rows={rows} loading={isLoading} />
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create Task</DialogTitle>
        <Box component="form" onSubmit={handleCreate}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12}><TextField fullWidth required label="Title" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} /></Grid>
              <Grid item xs={12}><TextField fullWidth multiline rows={3} label="Description" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} /></Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth><InputLabel>Priority</InputLabel>
                  <Select value={form.priority} label="Priority" onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}>
                    {['high', 'medium', 'low'].map((p) => <MenuItem key={p} value={p}>{p}</MenuItem>)}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}><TextField fullWidth label="Due Date" type="date" InputLabelProps={{ shrink: true }} value={form.due_date} onChange={(e) => setForm((f) => ({ ...f, due_date: e.target.value }))} /></Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={creating}>Create</Button>
          </DialogActions>
        </Box>
      </Dialog>
      <Dialog open={Boolean(completeTarget)} onClose={() => setCompleteTarget(null)}>
        <DialogTitle>Complete task?</DialogTitle>
        <DialogContent>{completeTarget?.title || 'This task'} will be marked as completed.</DialogContent>
        <DialogActions>
          <Button onClick={() => setCompleteTarget(null)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={async () => {
              await completeTask(completeTarget.id)
              setCompleteTarget(null)
            }}
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
