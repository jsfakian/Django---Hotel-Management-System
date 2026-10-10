import React, { useState } from 'react'
import {
  Box, Button, Paper, Typography, Grid, TextField, MenuItem,
  Dialog, DialogTitle, DialogContent, DialogActions,
  Table, TableHead, TableBody, TableRow, TableCell, Chip, Alert,
} from '@mui/material'
import { Add, Delete, Schedule } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import {
  useGetCustomReportsQuery,
  useCreateCustomReportMutation,
  useDeleteCustomReportMutation,
  useGetScheduledReportsQuery,
  useCreateScheduledReportMutation,
  useDeleteScheduledReportMutation,
  useGetReportExecutionsQuery,
} from '../../features/analytics/analyticsApi'

const REPORT_TYPES = ['occupancy', 'revenue', 'guest', 'booking', 'payment', 'custom']
const FREQUENCIES = ['daily', 'weekly', 'monthly']

const DASH = '—'
const listOf = (d) => d?.results || d || []
const fmtDate = (v, fn) => (v ? new Date(v)[fn]() : DASH)
const TABS = [
  { key: 'custom', label: 'Custom Reports' },
  { key: 'scheduled', label: 'Scheduled Reports' },
  { key: 'executions', label: 'Execution History' },
]
const EMPTY_REPORT_FORM = { name: '', report_type: 'revenue', filters: '{}', description: '' }
const EMPTY_SCHED_FORM = { name: '', report_type: 'revenue', frequency: 'weekly', recipients: '' }

function ReportsTable({ headers, emptyText, isEmpty, children }) {
  return (
    <Paper>
      <Table>
        <TableHead>
          <TableRow>{headers.map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow>
        </TableHead>
        <TableBody>
          {isEmpty && (
            <TableRow><TableCell colSpan={headers.length}><Typography color="text.secondary">{emptyText}</Typography></TableCell></TableRow>
          )}
          {children}
        </TableBody>
      </Table>
    </Paper>
  )
}

function ToolbarButton({ icon, label, onClick }) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
      <Button variant="contained" startIcon={icon} onClick={onClick}>{label}</Button>
    </Box>
  )
}

function CustomReportsTab({ reports, loading, error, onNew, onDelete }) {
  return (
    <>
      <ToolbarButton icon={<Add />} label="New Report" onClick={onNew} />
      {error && <ErrorAlert error={error} />}
      {loading ? <LoadingSpinner /> : (
        <ReportsTable headers={['Name', 'Type', 'Description', 'Created', '']} emptyText="No custom reports yet." isEmpty={reports.length === 0}>
          {reports.map((r) => (
            <TableRow key={r.id}>
              <TableCell>{r.name}</TableCell>
              <TableCell><Chip size="small" label={r.report_type} /></TableCell>
              <TableCell>{r.description || DASH}</TableCell>
              <TableCell>{fmtDate(r.created_at, 'toLocaleDateString')}</TableCell>
              <TableCell>
                <Button size="small" color="error" startIcon={<Delete />}
                  onClick={() => onDelete({ id: r.id, name: r.name, type: 'custom' })}>
                  Delete
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </ReportsTable>
      )}
    </>
  )
}

function ScheduledReportsTab({ reports, loading, onNew, onDelete }) {
  return (
    <>
      <ToolbarButton icon={<Schedule />} label="Schedule Report" onClick={onNew} />
      {loading ? <LoadingSpinner /> : (
        <ReportsTable headers={['Name', 'Type', 'Frequency', 'Recipients', 'Active', '']} emptyText="No scheduled reports." isEmpty={reports.length === 0}>
          {reports.map((r) => (
            <TableRow key={r.id}>
              <TableCell>{r.name}</TableCell>
              <TableCell><Chip size="small" label={r.report_type} /></TableCell>
              <TableCell>{r.frequency}</TableCell>
              <TableCell>{Array.isArray(r.recipients) ? r.recipients.join(', ') : r.recipients}</TableCell>
              <TableCell><Chip size="small" label={r.is_active ? 'Active' : 'Paused'} color={r.is_active ? 'success' : 'default'} /></TableCell>
              <TableCell>
                <Button size="small" color="error" onClick={() => onDelete({ id: r.id, name: r.name, type: 'scheduled' })}>Delete</Button>
              </TableCell>
            </TableRow>
          ))}
        </ReportsTable>
      )}
    </>
  )
}

const execColor = (status) => {
  if (status === 'success') return 'success'
  return status === 'failed' ? 'error' : 'info'
}

function ExecutionsTab({ executions }) {
  return (
    <ReportsTable headers={['Report', 'Status', 'Started', 'Completed', 'Message']} emptyText="No executions yet." isEmpty={executions.length === 0}>
      {executions.map((e) => (
        <TableRow key={e.id}>
          <TableCell>{e.report_name || e.report}</TableCell>
          <TableCell><Chip size="small" label={e.status} color={execColor(e.status)} /></TableCell>
          <TableCell>{fmtDate(e.started_at, 'toLocaleString')}</TableCell>
          <TableCell>{fmtDate(e.completed_at, 'toLocaleString')}</TableCell>
          <TableCell>{e.message || DASH}</TableCell>
        </TableRow>
      ))}
    </ReportsTable>
  )
}

function parseFilters(text) {
  try { return JSON.parse(text) } catch { return {} }
}

function CreateReportDialog({ open, onClose, onMessage }) {
  const [form, setForm] = useState(EMPTY_REPORT_FORM)
  const [createReport, { isLoading: creating }] = useCreateCustomReportMutation()
  const setField = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await createReport({ ...form, filters: parseFilters(form.filters) })
    if (result.error) {
      onMessage({ type: 'error', text: 'Failed to create report.' })
      return
    }
    onMessage({ type: 'success', text: 'Report created.' })
    onClose()
    setForm(EMPTY_REPORT_FORM)
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>New Custom Report</DialogTitle>
      <Box component="form" onSubmit={handleSubmit}>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField fullWidth required label="Name" value={form.name} onChange={setField('name')} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField select fullWidth label="Type" value={form.report_type} onChange={setField('report_type')}>
                {REPORT_TYPES.map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth multiline rows={2} label="Description" value={form.description} onChange={setField('description')} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Filters (JSON)" value={form.filters} onChange={setField('filters')} helperText='e.g. {"property": 1}' />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={creating}>Create</Button>
        </DialogActions>
      </Box>
    </Dialog>
  )
}

function ScheduleReportDialog({ open, onClose, onMessage }) {
  const [form, setForm] = useState(EMPTY_SCHED_FORM)
  const [createScheduled, { isLoading: scheduling }] = useCreateScheduledReportMutation()
  const setField = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await createScheduled({
      ...form,
      recipients: form.recipients.split(',').map((s) => s.trim()).filter(Boolean),
    })
    if (result.error) {
      onMessage({ type: 'error', text: 'Failed to schedule report.' })
      return
    }
    onMessage({ type: 'success', text: 'Report scheduled.' })
    onClose()
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Schedule Report</DialogTitle>
      <Box component="form" onSubmit={handleSubmit}>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField fullWidth required label="Name" value={form.name} onChange={setField('name')} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField select fullWidth label="Report Type" value={form.report_type} onChange={setField('report_type')}>
                {REPORT_TYPES.map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField select fullWidth label="Frequency" value={form.frequency} onChange={setField('frequency')}>
                {FREQUENCIES.map((f) => <MenuItem key={f} value={f}>{f}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Recipients (comma-separated emails)" value={form.recipients} onChange={setField('recipients')} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={scheduling}>Schedule</Button>
        </DialogActions>
      </Box>
    </Dialog>
  )
}

function DeleteReportDialog({ target, onClose }) {
  const [deleteReport, { isLoading: deleting }] = useDeleteCustomReportMutation()
  const [deleteScheduled] = useDeleteScheduledReportMutation()

  const handleDelete = async () => {
    if (target.type === 'custom') await deleteReport(target.id)
    else await deleteScheduled(target.id)
    onClose()
  }

  return (
    <Dialog open={Boolean(target)} onClose={onClose}>
      <DialogTitle>Delete &quot;{target?.name}&quot;?</DialogTitle>
      <DialogContent>This cannot be undone.</DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button color="error" disabled={deleting} onClick={handleDelete}>Delete</Button>
      </DialogActions>
    </Dialog>
  )
}

export default function CustomReportsPage() {
  const [tab, setTab] = useState('custom')
  const [createOpen, setCreateOpen] = useState(false)
  const [schedOpen, setSchedOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [msg, setMsg] = useState(null)

  const { data: reports, isLoading: loadingReports, error: reportsError } = useGetCustomReportsQuery()
  const { data: scheduled, isLoading: loadingSched } = useGetScheduledReportsQuery()
  const { data: executions } = useGetReportExecutionsQuery()

  return (
    <AppLayout>
      <Typography variant="h5" sx={{ mb: 3 }}>Reports</Typography>
      {msg && <Alert severity={msg.type} sx={{ mb: 2 }} onClose={() => setMsg(null)}>{msg.text}</Alert>}

      <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
        {TABS.map((t) => (
          <Button key={t.key} variant={tab === t.key ? 'contained' : 'outlined'} size="small" onClick={() => setTab(t.key)}>
            {t.label}
          </Button>
        ))}
      </Box>

      {tab === 'custom' && (
        <CustomReportsTab reports={listOf(reports)} loading={loadingReports} error={reportsError}
          onNew={() => setCreateOpen(true)} onDelete={setDeleteTarget} />
      )}
      {tab === 'scheduled' && (
        <ScheduledReportsTab reports={listOf(scheduled)} loading={loadingSched}
          onNew={() => setSchedOpen(true)} onDelete={setDeleteTarget} />
      )}
      {tab === 'executions' && <ExecutionsTab executions={listOf(executions)} />}

      <CreateReportDialog open={createOpen} onClose={() => setCreateOpen(false)} onMessage={setMsg} />
      <ScheduleReportDialog open={schedOpen} onClose={() => setSchedOpen(false)} onMessage={setMsg} />
      <DeleteReportDialog target={deleteTarget} onClose={() => setDeleteTarget(null)} />
    </AppLayout>
  )
}
