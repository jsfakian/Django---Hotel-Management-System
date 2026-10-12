import React, { useState } from 'react'
import { Grid, Paper, Divider, Table, TableBody, TableCell, TableHead, TableRow, Chip, Typography } from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import { AnalyticsFilters, AnalyticsHeader, KpiCard } from '../../components/analytics/AnalyticsFilters'
import { euro, pct, num, periodLabel } from '../../components/analytics/format'
import { useGetExecutiveOverviewQuery } from '../../features/analytics/analyticsApi'

function KpiGrid({ kpis }) {
  const items = [
    ['Room Revenue', euro(kpis.total_revenue), kpis.revenue_trend_pct],
    ['Occupancy Rate', pct(kpis.occupancy_rate), kpis.occupancy_trend_pct],
    ['ADR (Avg Daily Rate)', euro(kpis.adr, 2), kpis.adr_trend_pct],
    ['RevPAR', euro(kpis.revpar, 2), kpis.revpar_trend_pct],
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
    <Paper sx={{ ...sx, overflowX: 'auto' }}>
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

const trendRows = (trend) => [...trend].reverse().map((r) => [r.date, euro(r.revenue, 2), r.bookings, pct(r.occupancy)])
const topRows = (props) => props.map((p) => [p.name, euro(p.revenue, 2), pct(p.occupancy), euro(p.adr, 2), euro(p.revpar, 2)])
const fmtYoy = (metric, v) => (/occupancy/i.test(metric) ? pct(v) : euro(v, /adr|revpar/i.test(metric) ? 2 : 0))
const yoyRows = (yoy) => yoy.map((r) => [
  r.metric, fmtYoy(r.metric, r.this_year), fmtYoy(r.metric, r.last_year),
  r.change_pct === null || r.change_pct === undefined
    ? '—'
    : <Chip key="chg" size="small" label={`${r.change_pct > 0 ? '+' : ''}${num(r.change_pct).toFixed(1)}%`} color={r.change_pct >= 0 ? 'success' : 'error'} />,
])

export default function ExecutiveDashboard() {
  const [property, setProperty] = useState('')
  const [period, setPeriod] = useState('month')
  const { data = {}, isLoading, isFetching, error } = useGetExecutiveOverviewQuery({ property_id: property || undefined, period })

  return (
    <AppLayout>
      <AnalyticsHeader title="Executive Dashboard" subtitle={periodLabel(data)}>
        <AnalyticsFilters properties={data.properties || []} property={property} onPropertyChange={setProperty} period={period} onPeriodChange={setPeriod} />
      </AnalyticsHeader>
      {error && <ErrorAlert error={error} />}
      {isLoading || isFetching ? <LoadingSpinner /> : (
        <>
          <KpiGrid kpis={data.kpis || {}} />
          <TableSection title={period === 'year' ? 'Monthly Revenue' : 'Daily Revenue'} headers={['Date', 'Room revenue', 'Arrivals', 'Occupancy']} rows={trendRows(data.revenue_trend || [])} />
          <TableSection title="Properties" headers={['Property', 'Room revenue', 'Occupancy', 'ADR', 'RevPAR']} rows={topRows(data.top_properties || [])} />
          <TableSection title="Year-over-Year Comparison" headers={['Metric', 'This period', 'Same period last year', 'Change']} rows={yoyRows(data.year_over_year || [])} />
        </>
      )}
    </AppLayout>
  )
}
