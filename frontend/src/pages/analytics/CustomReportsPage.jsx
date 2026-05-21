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

export default function CustomReportsPage() {
  const [tab, setTab] = useState('custom')
  const [createOpen, setCreateOpen] = useState(false)
  const [schedOpen, setSchedOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [form, setForm] = useState({ name: '', report_type: 'revenue', filters: '{}', description: '' })
  const [schedForm, setSchedForm] = useState({ name: '', report_type: 'revenue', frequency: 'weekly', recipients: '' })
  const [msg, setMsg] = useState(null)

  const { data: reports, isLoading: loadingReports, error: reportsError } = useGetCustomReportsQuery()
  const { data: scheduled, isLoading: loadingSched } = useGetScheduledReportsQuery()
  const { data: executions } = useGetReportExecutionsQuery()
  const [createReport, { isLoading: creating }] = useCreateCustomReportMutation()
  const [deleteReport, { isLoading: deleting }] = useDeleteCustomReportMutation()
  const [createScheduled, { isLoading: scheduling }] = useCreateScheduledReportMutation()
  const [deleteScheduled] = useDeleteScheduledReportMutation()

  const customReports = reports?.results || reports || []
  const scheduledReports = scheduled?.results || scheduled || []
  const execList = executions?.results || executions || []

  const handleCreateReport = async (e) => {
    e.preventDefault()
    let filters = {}
    try { filters = JSON.parse(form.filters) } catch { filters = {} }
    const result = await createReport({ ...form, filters })
    if (result.error) {
      setMsg({ type: 'error', text: 'Failed to create report.' })
    } else {
      setMsg({ type: 'success', text: 'Report created.' })
      setCreateOpen(false)
      setForm({ name: '', report_type: 'revenue', filters: '{}', description: '' })
    }
  }

  const handleCreateScheduled = async (e) => {
    e.preventDefault()
    const result = await createScheduled({
      ...schedForm,
      recipients: schedForm.recipients.split(',').map((s) => s.trim()).filter(Boolean),
    })
    if (result.error) {
      setMsg({ type: 'error', text: 'Failed to schedule report.' })
    } else {
      setMsg({ type: 'success', text: 'Report scheduled.' })
      setSchedOpen(false)
    }
  }

  const TABS = [
    { key: 'custom', label: 'Custom Reports' },
    { key: 'scheduled', label: 'Scheduled Reports' },
    { key: 'executions', label: 'Execution History' },
  ]

  return (
    <AppLayout>
      <Typography variant="h5" sx={{ mb: 3 }}>Reports</Typography>
      {msg && <Alert severity={msg.type} sx={{ mb: 2 }} onClose={() => setMsg(null)}>{msg.text}</Alert>}

      {/* Tab bar */}
      <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
        {TABS.map((t) => (
          <Button key={t.key} variant={tab === t.key ? 'contained' : 'outlined'} size="small" onClick={() => setTab(t.key)}>
            {t.label}
          </Button>
        ))}
      </Box>

      {/* Custom Reports */}
      {tab === 'custom' && (
        <>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button variant="contained" startIcon={<Add />} onClick={() => setCreateOpen(true)}>New Report</Button>
          </Box>
          {reportsError && <ErrorAlert error={reportsError} />}
          {loadingReports ? <LoadingSpinner /> : (
            <Paper>
              <Table>
                <TableHead>
                  <TableRow>{['Name', 'Type', 'Description', 'Created', ''].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow>
                </TableHead>
                <TableBody>
                  {customReports.length === 0 && (
                    <TableRow><TableCell colSpan={5}><Typography color="text.secondary">No custom reports yet.</Typography></TableCell></TableRow>
                  )}
                  {customReports.map((r) => (
                    <TableRow key={r.id}>
                      <TableCell>{r.name}</TableCell>
                      <TableCell><Chip size="small" label={r.report_type} /></TableCell>
                      <TableCell>{r.description || '—'}</TableCell>
                      <TableCell>{r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}</TableCell>
                      <TableCell>
                        <Button size="small" color="error" startIcon={<Delete />}
                          onClick={() => setDeleteTarget({ id: r.id, name: r.name, type: 'custom' })}>
                          Delete
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>
          )}
        </>
      )}

      {/* Scheduled Reports */}
      {tab === 'scheduled' && (
        <>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button variant="contained" startIcon={<Schedule />} onClick={() => setSchedOpen(true)}>Schedule Report</Button>
          </Box>
          {loadingSched ? <LoadingSpinner /> : (
            <Paper>
              <Table>
                <TableHead>
                  <TableRow>{['Name', 'Type', 'Frequency', 'Recipients', 'Active', ''].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow>
                </TableHead>
                <TableBody>
                  {scheduledReports.length === 0 && (
                    <TableRow><TableCell colSpan={6}><Typography color="text.secondary">No scheduled reports.</Typography></TableCell></TableRow>
                  )}
                  {scheduledReports.map((r) => (
                    <TableRow key={r.id}>
                      <TableCell>{r.name}</TableCell>
                      <TableCell><Chip size="small" label={r.report_type} /></TableCell>
                      <TableCell>{r.frequency}</TableCell>
                      <TableCell>{Array.isArray(r.recipients) ? r.recipients.join(', ') : r.recipients}</TableCell>
                      <TableCell><Chip size="small" label={r.is_active ? 'Active' : 'Paused'} color={r.is_active ? 'success' : 'default'} /></TableCell>
                      <TableCell>
                        <Button size="small" color="error" onClick={() => setDeleteTarget({ id: r.id, name: r.name, type: 'scheduled' })}>Delete</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Paper>
          )}
        </>
      )}

      {/* Execution History */}
      {tab === 'executions' && (
        <Paper>
          <Table>
            <TableHead>
              <TableRow>{['Report', 'Status', 'Started', 'Completed', 'Message'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow>
            </TableHead>
            <TableBody>
              {execList.length === 0 && (
                <TableRow><TableCell colSpan={5}><Typography color="text.secondary">No executions yet.</Typography></TableCell></TableRow>
              )}
              {execList.map((e) => (
                <TableRow key={e.id}>
                  <TableCell>{e.report_name || e.report}</TableCell>
                  <TableCell><Chip size="small" label={e.status} color={e.status === 'success' ? 'success' : e.status === 'failed' ? 'error' : 'info'} /></TableCell>
                  <TableCell>{e.started_at ? new Date(e.started_at).toLocaleString() : '—'}</TableCell>
                  <TableCell>{e.completed_at ? new Date(e.completed_at).toLocaleString() : '—'}</TableCell>
                  <TableCell>{e.message || '—'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {/* Create Report Dialog */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>New Custom Report</DialogTitle>
        <Box component="form" onSubmit={handleCreateReport}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField fullWidth required label="Name" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField select fullWidth label="Type" value={form.report_type} onChange={(e) => setForm((f) => ({ ...f, report_type: e.target.value }))}>
                  {REPORT_TYPES.map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid item xs={12}>
                <TextField fullWidth multiline rows={2} label="Description" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
              </Grid>
              <Grid item xs={12}>
                <TextField fullWidth label="Filters (JSON)" value={form.filters} onChange={(e) => setForm((f) => ({ ...f, filters: e.target.value }))} helperText='e.g. {"property": 1}' />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={creating}>Create</Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Schedule Report Dialog */}
      <Dialog open={schedOpen} onClose={() => setSchedOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Schedule Report</DialogTitle>
        <Box component="form" onSubmit={handleCreateScheduled}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField fullWidth required label="Name" value={schedForm.name} onChange={(e) => setSchedForm((f) => ({ ...f, name: e.target.value }))} />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField select fullWidth label="Report Type" value={schedForm.report_type} onChange={(e) => setSchedForm((f) => ({ ...f, report_type: e.target.value }))}>
                  {REPORT_TYPES.map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField select fullWidth label="Frequency" value={schedForm.frequency} onChange={(e) => setSchedForm((f) => ({ ...f, frequency: e.target.value }))}>
                  {FREQUENCIES.map((f) => <MenuItem key={f} value={f}>{f}</MenuItem>)}
                </TextField>
              </Grid>
              <Grid item xs={12}>
                <TextField fullWidth label="Recipients (comma-separated emails)" value={schedForm.recipients} onChange={(e) => setSchedForm((f) => ({ ...f, recipients: e.target.value }))} />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSchedOpen(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={scheduling}>Schedule</Button>
          </DialogActions>
        </Box>
      </Dialog>

      {/* Delete Confirm */}
      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Delete "{deleteTarget?.name}"?</DialogTitle>
        <DialogContent>This cannot be undone.</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancel</Button>
          <Button color="error" disabled={deleting}
            onClick={async () => {
              if (deleteTarget.type === 'custom') await deleteReport(deleteTarget.id)
              else await deleteScheduled(deleteTarget.id)
              setDeleteTarget(null)
            }}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </AppLayout>
  )
}
