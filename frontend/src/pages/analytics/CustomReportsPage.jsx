import React, { useState } from 'react'
import {
  Box, Button, Paper, Typography, Grid, TextField, MenuItem,
  Dialog, DialogTitle, DialogContent, DialogActions, IconButton, Tooltip,
  Table, TableHead, TableBody, TableRow, TableCell, Chip, Alert,
} from '@mui/material'
import { Add, Delete, Schedule, PlayArrow, Visibility, Download, Refresh } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import { downloadFile } from '../../services/downloadFile'
import { useGetPropertiesQuery } from '../../features/properties/propertiesApi'
import {
  useGetCustomReportsQuery,
  useCreateCustomReportMutation,
  useDeleteCustomReportMutation,
  useGenerateCustomReportMutation,
  useGetCustomReportDataQuery,
  useGetScheduledReportsQuery,
  useCreateScheduledReportMutation,
  useDeleteScheduledReportMutation,
  useTriggerScheduledReportMutation,
  useGetReportExecutionsQuery,
} from '../../features/analytics/analyticsApi'

const REPORT_TYPES = [
  ['revenue', 'Revenue'], ['occupancy', 'Occupancy'], ['guest', 'Guests'], ['booking', 'Bookings'],
  ['payment', 'Payments'], ['pricing', 'Pricing'], ['custom', 'Executive summary'],
]
const SCHEDULED_TYPES = [
  ['daily_operational', 'Daily Operational Dashboard'], ['daily_finance', 'Daily Finance Report'],
  ['weekly_performance', 'Weekly Performance Report'], ['weekly_marketing', 'Weekly Marketing Report'],
  ['monthly_executive', 'Monthly Executive Summary'], ['monthly_occupancy', 'Monthly Occupancy Analysis'],
  ['compliance', 'Compliance Report'], ['custom', 'Custom Report'],
]
const SCHEDULE_TYPES = [['daily', 'Daily'], ['weekly', 'Weekly'], ['monthly', 'Monthly']]
const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const FORMATS = [['csv', 'CSV'], ['excel', 'Excel (XLSX)'], ['pdf', 'PDF']]
const FILE_EXT = { csv: 'csv', excel: 'xlsx', pdf: 'pdf' }

const DASH = '—'
const listOf = (d) => d?.results || (Array.isArray(d) ? d : [])
const labelOf = (pairs, value) => (pairs.find(([v]) => v === value) || [value, value])[1]
const fmtDate = (v, fn = 'toLocaleString') => (v ? new Date(v)[fn]() : DASH)
const isoDay = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const STATUS_COLORS = { generated: 'success', failed: 'error', pending: 'default', generating: 'info', sent: 'success', error: 'error' }

const TABS = [
  { key: 'custom', label: 'Custom Reports' },
  { key: 'scheduled', label: 'Scheduled Reports' },
  { key: 'executions', label: 'Execution History' },
]

function emptyReportForm() {
  const today = new Date()
  return {
    name: '', report_type: 'revenue', property: '', description: '', export_format: 'csv',
    from_date: isoDay(new Date(today.getFullYear(), today.getMonth(), 1)), to_date: isoDay(today),
  }
}
const EMPTY_SCHED_FORM = {
  name: '', property: '', report_type: 'weekly_performance', schedule_type: 'weekly',
  schedule_dow: 0, schedule_day: 1, schedule_time: '07:00', recipients: '', export_format: 'pdf',
}

function ReportsTable({ headers, emptyText, isEmpty, children }) {
  return (
    <Paper sx={{ overflowX: 'auto' }}>
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

function ActionIcon({ title, onClick, disabled, color, children }) {
  return (
    <Tooltip title={title}>
      <span><IconButton size="small" color={color} onClick={onClick} disabled={disabled}>{children}</IconButton></span>
    </Tooltip>
  )
}

function CustomReportsTab({ reports, loading, error, onNew, onDelete, onPreview, onMessage }) {
  const [generate, { isLoading: generating, originalArgs: generatingId }] = useGenerateCustomReportMutation()

  const handleGenerate = async (r) => {
    const result = await generate(r.id)
    if (result.error || result.data?.status === 'failed') {
      onMessage({ type: 'error', text: result.data?.error_message || `Could not generate "${r.name}".` })
    } else {
      onMessage({ type: 'success', text: `"${r.name}" generated.` })
    }
  }

  const handleDownload = async (r) => {
    try {
      await downloadFile(`/analytics/custom-reports/${r.id}/download/`, `${r.name.replace(/[^\w-]+/g, '_')}.${FILE_EXT[r.export_format] || 'csv'}`)
    } catch {
      onMessage({ type: 'error', text: 'Download failed. Generate the report first.' })
    }
  }

  return (
    <>
      <ToolbarButton icon={<Add />} label="New Report" onClick={onNew} />
      {error && <ErrorAlert error={error} />}
      {loading ? <LoadingSpinner /> : (
        <ReportsTable headers={['Name', 'Type', 'Property', 'Period', 'Status', 'Generated', '']} emptyText="No custom reports yet." isEmpty={reports.length === 0}>
          {reports.map((r) => (
            <TableRow key={r.id}>
              <TableCell>
                <Typography variant="body2" fontWeight={600}>{r.name}</Typography>
                {r.description && <Typography variant="caption" color="text.secondary">{r.description}</Typography>}
              </TableCell>
              <TableCell><Chip size="small" label={labelOf(REPORT_TYPES, r.report_type)} /></TableCell>
              <TableCell>{r.property_name || 'All properties'}</TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap' }}>{r.from_date} → {r.to_date}</TableCell>
              <TableCell>
                <Tooltip title={r.error_message || ''}><Chip size="small" label={r.status} color={STATUS_COLORS[r.status] || 'default'} /></Tooltip>
              </TableCell>
              <TableCell>{fmtDate(r.generated_at)}</TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap' }}>
                <ActionIcon title={r.status === 'generated' ? 'Regenerate' : 'Generate'} onClick={() => handleGenerate(r)} disabled={generating && generatingId === r.id}>
                  {r.status === 'generated' ? <Refresh fontSize="small" /> : <PlayArrow fontSize="small" />}
                </ActionIcon>
                <ActionIcon title="Preview" onClick={() => onPreview(r)}><Visibility fontSize="small" /></ActionIcon>
                <ActionIcon title={`Download ${labelOf(FORMATS, r.export_format)}`} onClick={() => handleDownload(r)} disabled={r.status !== 'generated'}><Download fontSize="small" /></ActionIcon>
                <ActionIcon title="Delete" color="error" onClick={() => onDelete({ id: r.id, name: r.name, type: 'custom' })}><Delete fontSize="small" /></ActionIcon>
              </TableCell>
            </TableRow>
          ))}
        </ReportsTable>
      )}
    </>
  )
}

function scheduleText(r) {
  const time = (r.schedule_time || '').slice(0, 5)
  if (r.schedule_type === 'weekly') return `Weekly · ${WEEKDAYS[r.schedule_dow ?? 0]} ${time}`
  if (r.schedule_type === 'monthly') return `Monthly · day ${r.schedule_day || 1} ${time}`
  return `${labelOf(SCHEDULE_TYPES, r.schedule_type)} ${time}`
}

function ScheduledReportsTab({ reports, loading, onNew, onDelete, onMessage }) {
  const [trigger, { isLoading: triggering }] = useTriggerScheduledReportMutation()

  const handleTrigger = async (r) => {
    const result = await trigger({ id: r.id })
    onMessage(result.error
      ? { type: 'error', text: `Could not run "${r.name}".` }
      : { type: 'success', text: `"${r.name}" queued — see Execution History.` })
  }

  return (
    <>
      <ToolbarButton icon={<Schedule />} label="Schedule Report" onClick={onNew} />
      {loading ? <LoadingSpinner /> : (
        <ReportsTable headers={['Name', 'Type', 'Property', 'Schedule', 'Recipients', 'Next run', 'Active', '']} emptyText="No scheduled reports." isEmpty={reports.length === 0}>
          {reports.map((r) => (
            <TableRow key={r.id}>
              <TableCell>{r.name}</TableCell>
              <TableCell><Chip size="small" label={labelOf(SCHEDULED_TYPES, r.report_type)} /></TableCell>
              <TableCell>{r.property_name || DASH}</TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap' }}>{scheduleText(r)} {r.timezone || ''}</TableCell>
              <TableCell>{(r.recipient_emails || []).join(', ') || DASH}</TableCell>
              <TableCell>{fmtDate(r.next_scheduled_at)}</TableCell>
              <TableCell><Chip size="small" label={r.is_active ? 'Active' : 'Paused'} color={r.is_active ? 'success' : 'default'} /></TableCell>
              <TableCell sx={{ whiteSpace: 'nowrap' }}>
                <ActionIcon title="Run now" onClick={() => handleTrigger(r)} disabled={triggering}><PlayArrow fontSize="small" /></ActionIcon>
                <ActionIcon title="Delete" color="error" onClick={() => onDelete({ id: r.id, name: r.name, type: 'scheduled' })}><Delete fontSize="small" /></ActionIcon>
              </TableCell>
            </TableRow>
          ))}
        </ReportsTable>
      )}
    </>
  )
}

function ExecutionsTab({ executions }) {
  return (
    <ReportsTable headers={['Report', 'Status', 'Email', 'Data period', 'Run at', 'Duration', 'Message']} emptyText="No executions yet." isEmpty={executions.length === 0}>
      {executions.map((e) => (
        <TableRow key={e.id}>
          <TableCell>{e.scheduled_report_name || e.scheduled_report}</TableCell>
          <TableCell><Chip size="small" label={e.execution_status} color={STATUS_COLORS[e.execution_status] || 'default'} /></TableCell>
          <TableCell><Chip size="small" variant="outlined" label={e.email_status || DASH} color={STATUS_COLORS[e.email_status] || 'default'} /></TableCell>
          <TableCell sx={{ whiteSpace: 'nowrap' }}>{e.data_date_from} → {e.data_date_to}</TableCell>
          <TableCell>{fmtDate(e.created_at)}</TableCell>
          <TableCell>{e.execution_time_seconds != null ? `${Number(e.execution_time_seconds).toFixed(1)}s` : DASH}</TableCell>
          <TableCell>{e.error_message || DASH}</TableCell>
        </TableRow>
      ))}
    </ReportsTable>
  )
}

function PropertyField({ value, onChange, properties, allowAll, required }) {
  return (
    <TextField select fullWidth required={required} label="Property" value={value} onChange={onChange}>
      {allowAll && <MenuItem value="">All properties</MenuItem>}
      {properties.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
    </TextField>
  )
}

function CreateReportDialog({ open, onClose, onMessage, properties }) {
  const [form, setForm] = useState(emptyReportForm)
  const [createReport, { isLoading: creating }] = useCreateCustomReportMutation()
  const [generate, { isLoading: generating }] = useGenerateCustomReportMutation()
  const setField = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await createReport({ ...form, property: form.property || null })
    if (result.error) {
      const details = result.error?.data?.error?.details
      const text = Array.isArray(details) && details.length
        ? details.map((d) => `${d.field}: ${d.message}`).join('; ')
        : 'Failed to create report.'
      onMessage({ type: 'error', text })
      return
    }
    const gen = await generate(result.data.id)
    onMessage(gen.error || gen.data?.status === 'failed'
      ? { type: 'warning', text: 'Report created, but generation failed. Try Generate again.' }
      : { type: 'success', text: `"${form.name}" is ready — preview or download it below.` })
    onClose()
    setForm(emptyReportForm())
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>New Custom Report</DialogTitle>
      <Box component="form" onSubmit={handleSubmit}>
        <DialogContent>
          <Grid container spacing={2} sx={{ pt: 1 }}>
            <Grid item xs={12}>
              <TextField fullWidth required label="Name" value={form.name} onChange={setField('name')} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField select fullWidth label="Type" value={form.report_type} onChange={setField('report_type')}>
                {REPORT_TYPES.map(([v, l]) => <MenuItem key={v} value={v}>{l}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <PropertyField value={form.property} onChange={setField('property')} properties={properties} allowAll />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth required type="date" label="From" value={form.from_date} onChange={setField('from_date')} InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth required type="date" label="To" value={form.to_date} onChange={setField('to_date')} InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField select fullWidth label="Export format" value={form.export_format} onChange={setField('export_format')}>
                {FORMATS.map(([v, l]) => <MenuItem key={v} value={v}>{l}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth multiline rows={2} label="Description" value={form.description} onChange={setField('description')} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={creating || generating}>{generating ? 'Generating…' : 'Create & generate'}</Button>
        </DialogActions>
      </Box>
    </Dialog>
  )
}

function ScheduleReportDialog({ open, onClose, onMessage, properties }) {
  const [form, setForm] = useState(EMPTY_SCHED_FORM)
  const [createScheduled, { isLoading: scheduling }] = useCreateScheduledReportMutation()
  const setField = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const { recipients, export_format: exportFormat, ...rest } = form
    const result = await createScheduled({
      ...rest,
      property: form.property || properties[0]?.id,
      schedule_dow: form.schedule_type === 'weekly' ? Number(form.schedule_dow) : null,
      schedule_day: form.schedule_type === 'monthly' ? Number(form.schedule_day) : null,
      recipient_emails: recipients.split(',').map((s) => s.trim()).filter(Boolean),
      export_formats: [exportFormat],
      is_active: true,
    })
    if (result.error) {
      const details = result.error?.data?.error?.details
      onMessage({ type: 'error', text: Array.isArray(details) && details.length ? details.map((d) => `${d.field}: ${d.message}`).join('; ') : 'Failed to schedule report.' })
      return
    }
    onMessage({ type: 'success', text: 'Report scheduled.' })
    setForm(EMPTY_SCHED_FORM)
    onClose()
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Schedule Report</DialogTitle>
      <Box component="form" onSubmit={handleSubmit}>
        <DialogContent>
          <Grid container spacing={2} sx={{ pt: 1 }}>
            <Grid item xs={12}>
              <TextField fullWidth required label="Name" value={form.name} onChange={setField('name')} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <PropertyField value={form.property || properties[0]?.id || ''} onChange={setField('property')} properties={properties} required />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField select fullWidth label="Report Type" value={form.report_type} onChange={setField('report_type')}>
                {SCHEDULED_TYPES.map(([v, l]) => <MenuItem key={v} value={v}>{l}</MenuItem>)}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField select fullWidth label="Frequency" value={form.schedule_type} onChange={setField('schedule_type')}>
                {SCHEDULE_TYPES.map(([v, l]) => <MenuItem key={v} value={v}>{l}</MenuItem>)}
              </TextField>
            </Grid>
            {form.schedule_type === 'weekly' && (
              <Grid item xs={12} sm={4}>
                <TextField select fullWidth label="Day" value={form.schedule_dow} onChange={setField('schedule_dow')}>
                  {WEEKDAYS.map((d, i) => <MenuItem key={d} value={i}>{d}</MenuItem>)}
                </TextField>
              </Grid>
            )}
            {form.schedule_type === 'monthly' && (
              <Grid item xs={12} sm={4}>
                <TextField fullWidth type="number" label="Day of month" value={form.schedule_day} onChange={setField('schedule_day')} inputProps={{ min: 1, max: 28 }} />
              </Grid>
            )}
            <Grid item xs={12} sm={4}>
              <TextField fullWidth required type="time" label="Time (UTC)" value={form.schedule_time} onChange={setField('schedule_time')} InputLabelProps={{ shrink: true }} />
            </Grid>
            <Grid item xs={12} sm={8}>
              <TextField fullWidth label="Recipients (comma-separated emails)" value={form.recipients} onChange={setField('recipients')} />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField select fullWidth label="Format" value={form.export_format} onChange={setField('export_format')}>
                {FORMATS.map(([v, l]) => <MenuItem key={v} value={v}>{l}</MenuItem>)}
              </TextField>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" disabled={scheduling || !properties.length}>Schedule</Button>
        </DialogActions>
      </Box>
    </Dialog>
  )
}

const PREVIEW_LIMIT = 200

function PreviewTable({ columns, rows }) {
  if (rows.length === 0) return <Typography color="text.secondary">No rows for this period.</Typography>
  return (
    <Box sx={{ overflowX: 'auto' }}>
      <Table size="small" stickyHeader>
        <TableHead><TableRow>{columns.map((c) => <TableCell key={c.field} sx={{ fontWeight: 600 }}>{c.header}</TableCell>)}</TableRow></TableHead>
        <TableBody>
          {rows.slice(0, PREVIEW_LIMIT).map((row, i) => (
            <TableRow key={i}>{columns.map((c) => <TableCell key={c.field}>{row[c.field] ?? DASH}</TableCell>)}</TableRow>
          ))}
        </TableBody>
      </Table>
      {rows.length > PREVIEW_LIMIT && (
        <Typography variant="caption" color="text.secondary">Showing {PREVIEW_LIMIT} of {rows.length} rows — download for the full report.</Typography>
      )}
    </Box>
  )
}

function PreviewBody({ data }) {
  const summary = Object.entries(data?.summary || {})
  return (
    <>
      {summary.length > 0 && (
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {summary.map(([k, v]) => <Chip key={k} label={`${k}: ${v}`} />)}
        </Box>
      )}
      <PreviewTable columns={data?.columns || []} rows={data?.rows || []} />
    </>
  )
}

const reportSubtitle = (r) => (r ? `${labelOf(REPORT_TYPES, r.report_type)} · ${r.property_name || 'All properties'} · ${r.from_date} → ${r.to_date}` : '')

function PreviewDialog({ report, onClose }) {
  const { data, isLoading, isFetching, error } = useGetCustomReportDataQuery(report?.id, { skip: !report })
  return (
    <Dialog open={Boolean(report)} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        {report?.name}
        <Typography variant="body2" color="text.secondary">{reportSubtitle(report)}</Typography>
      </DialogTitle>
      <DialogContent dividers>
        {error && <ErrorAlert error={error} />}
        {isLoading || isFetching ? <LoadingSpinner /> : <PreviewBody data={data} />}
      </DialogContent>
      <DialogActions><Button onClick={onClose}>Close</Button></DialogActions>
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
  const [previewTarget, setPreviewTarget] = useState(null)
  const [msg, setMsg] = useState(null)

  const { data: reports, isLoading: loadingReports, error: reportsError } = useGetCustomReportsQuery()
  const { data: scheduled, isLoading: loadingSched } = useGetScheduledReportsQuery()
  const { data: executions } = useGetReportExecutionsQuery()
  const { data: propertiesData } = useGetPropertiesQuery({ page_size: 100 })
  const properties = listOf(propertiesData)

  return (
    <AppLayout>
      <Typography variant="h5" sx={{ mb: 3 }}>Reports</Typography>
      {msg && <Alert severity={msg.type} sx={{ mb: 2 }} onClose={() => setMsg(null)}>{msg.text}</Alert>}

      <Box sx={{ display: 'flex', gap: 1, mb: 3, flexWrap: 'wrap' }}>
        {TABS.map((t) => (
          <Button key={t.key} variant={tab === t.key ? 'contained' : 'outlined'} size="small" onClick={() => setTab(t.key)}>
            {t.label}
          </Button>
        ))}
      </Box>

      {tab === 'custom' && (
        <CustomReportsTab reports={listOf(reports)} loading={loadingReports} error={reportsError}
          onNew={() => setCreateOpen(true)} onDelete={setDeleteTarget} onPreview={setPreviewTarget} onMessage={setMsg} />
      )}
      {tab === 'scheduled' && (
        <ScheduledReportsTab reports={listOf(scheduled)} loading={loadingSched}
          onNew={() => setSchedOpen(true)} onDelete={setDeleteTarget} onMessage={setMsg} />
      )}
      {tab === 'executions' && <ExecutionsTab executions={listOf(executions)} />}

      <CreateReportDialog open={createOpen} onClose={() => setCreateOpen(false)} onMessage={setMsg} properties={properties} />
      <ScheduleReportDialog open={schedOpen} onClose={() => setSchedOpen(false)} onMessage={setMsg} properties={properties} />
      <PreviewDialog report={previewTarget} onClose={() => setPreviewTarget(null)} />
      <DeleteReportDialog target={deleteTarget} onClose={() => setDeleteTarget(null)} />
    </AppLayout>
  )
}
