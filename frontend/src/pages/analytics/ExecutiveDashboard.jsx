import React, { useState } from 'react'
import { Box, Grid, Card, CardContent, Typography, FormControl, InputLabel, Select, MenuItem, Paper, Divider, Table, TableBody, TableCell, TableHead, TableRow, Chip } from '@mui/material'
import { TrendingUp, TrendingDown } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetExecutiveDashboardQuery } from '../../features/analytics/analyticsApi'

function KpiCard({ title, value, trend }) {
  const isUp = trend > 0
  return (
    <Card>
      <CardContent>
        <Typography variant="body2" color="text.secondary">{title}</Typography>
        <Typography variant="h4" fontWeight={700} sx={{ my: 1 }}>{value}</Typography>
        {trend !== undefined && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {isUp ? <TrendingUp color="success" fontSize="small" /> : <TrendingDown color="error" fontSize="small" />}
            <Typography variant="body2" color={isUp ? 'success.main' : 'error.main'}>{Math.abs(trend)}%</Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

const num = (v) => Number(v || 0)

function KpiGrid({ kpis }) {
  const items = [
    ['Total Revenue', `€${num(kpis.total_revenue).toLocaleString()}`, kpis.revenue_trend_pct],
    ['Occupancy Rate', `${num(kpis.occupancy_rate).toFixed(1)}%`, kpis.occupancy_trend_pct],
    ['ADR (Avg Daily Rate)', `€${num(kpis.adr).toFixed(2)}`, kpis.adr_trend_pct],
    ['RevPAR', `€${num(kpis.revpar).toFixed(2)}`, kpis.revpar_trend_pct],
  ]
  return (
    <Grid container spacing={2} sx={{ mb: 4 }}>
      {items.map(([title, value, trend]) => (
        <Grid item xs={12} sm={6} md={3} key={title}><KpiCard title={title} value={value} trend={trend} /></Grid>
      ))}
    </Grid>
  )
}

function TableSection({ title, headers, rows, sx = { p: 2, mb: 3 } }) {
  if (rows.length === 0) return null
  return (
    <Paper sx={sx}>
      <Typography variant="h6" gutterBottom>{title}</Typography>
      <Divider sx={{ mb: 2 }} />
      <Table size="small">
        <TableHead><TableRow>{headers.map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
        <TableBody>
          {rows.map((cells, i) => <TableRow key={i}>{cells.map((c, j) => <TableCell key={j}>{c}</TableCell>)}</TableRow>)}
        </TableBody>
      </Table>
    </Paper>
  )
}

const trendRows = (trend) => trend.map((r) => [r.date, `€${num(r.revenue).toFixed(2)}`, r.bookings, `${num(r.occupancy).toFixed(1)}%`])
const topRows = (props) => props.map((p) => [p.name, `€${num(p.revenue).toFixed(2)}`, `${num(p.occupancy).toFixed(1)}%`, `€${num(p.adr).toFixed(2)}`])
const yoyRows = (yoy) => yoy.map((r) => [
  r.metric, r.this_year, r.last_year,
  <Chip key="chg" size="small" label={`${r.change_pct > 0 ? '+' : ''}${r.change_pct}%`} color={r.change_pct >= 0 ? 'success' : 'error'} />,
])

function PeriodSelect({ period, onChange }) {
  return (
    <Box sx={{ display: 'flex', gap: 2 }}>
      <FormControl size="small" sx={{ minWidth: 120 }}>
        <InputLabel>Period</InputLabel>
        <Select value={period} label="Period" onChange={(e) => onChange(e.target.value)}>
          {['day', 'week', 'month', 'year'].map((p) => <MenuItem key={p} value={p}>{p}</MenuItem>)}
        </Select>
      </FormControl>
    </Box>
  )
}

export default function ExecutiveDashboard() {
  const [property] = useState('')
  const [period, setPeriod] = useState('month')
  const { data = {}, isLoading, error } = useGetExecutiveDashboardQuery({ property: property || undefined, period })

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Executive Dashboard</Typography>
        <PeriodSelect period={period} onChange={setPeriod} />
      </Box>
      {error && <ErrorAlert error={error} />}
      <KpiGrid kpis={data.kpis || {}} />
      <TableSection title="Revenue Trend" headers={['Date', 'Revenue (€)', 'Bookings', 'Occupancy %']} rows={trendRows(data.revenue_trend || [])} />
      <TableSection title="Top Properties" headers={['Property', 'Revenue (€)', 'Occupancy %', 'ADR (€)']} rows={topRows(data.top_properties || [])} />
      <TableSection title="Year-over-Year Comparison" headers={['Metric', 'This Year', 'Last Year', 'Change %']} rows={yoyRows(data.year_over_year || [])} sx={{ p: 2 }} />
    </AppLayout>
  )
}
