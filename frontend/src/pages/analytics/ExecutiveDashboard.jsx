import React, { useState } from 'react'
import { Box, Grid, Card, CardContent, Typography, FormControl, InputLabel, Select, MenuItem, Paper, Divider, Table, TableBody, TableCell, TableHead, TableRow, Chip } from '@mui/material'
import { TrendingUp, TrendingDown } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetExecutiveDashboardQuery } from '../../features/analytics/analyticsApi'

function KpiCard({ title, value, trend, color }) {
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

export default function ExecutiveDashboard() {
  const [property, setProperty] = useState('')
  const [period, setPeriod] = useState('month')
  const { data, isLoading, error } = useGetExecutiveDashboardQuery({ property: property || undefined, period })

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>

  const kpis = data?.kpis || {}
  const trend = data?.revenue_trend || []
  const topProps = data?.top_properties || []
  const yoy = data?.year_over_year || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Executive Dashboard</Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Period</InputLabel>
            <Select value={period} label="Period" onChange={(e) => setPeriod(e.target.value)}>
              {['day', 'week', 'month', 'year'].map((p) => <MenuItem key={p} value={p}>{p}</MenuItem>)}
            </Select>
          </FormControl>
        </Box>
      </Box>
      {error && <ErrorAlert error={error} />}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}><KpiCard title="Total Revenue" value={`€${Number(kpis.total_revenue || 0).toLocaleString()}`} trend={kpis.revenue_trend_pct} /></Grid>
        <Grid item xs={12} sm={6} md={3}><KpiCard title="Occupancy Rate" value={`${Number(kpis.occupancy_rate || 0).toFixed(1)}%`} trend={kpis.occupancy_trend_pct} /></Grid>
        <Grid item xs={12} sm={6} md={3}><KpiCard title="ADR (Avg Daily Rate)" value={`€${Number(kpis.adr || 0).toFixed(2)}`} trend={kpis.adr_trend_pct} /></Grid>
        <Grid item xs={12} sm={6} md={3}><KpiCard title="RevPAR" value={`€${Number(kpis.revpar || 0).toFixed(2)}`} trend={kpis.revpar_trend_pct} /></Grid>
      </Grid>
      {trend.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Revenue Trend</Typography>
          <Divider sx={{ mb: 2 }} />
          <Table size="small">
            <TableHead><TableRow>{['Date', 'Revenue (€)', 'Bookings', 'Occupancy %'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
            <TableBody>{trend.map((row, i) => <TableRow key={i}><TableCell>{row.date}</TableCell><TableCell>€{Number(row.revenue || 0).toFixed(2)}</TableCell><TableCell>{row.bookings}</TableCell><TableCell>{Number(row.occupancy || 0).toFixed(1)}%</TableCell></TableRow>)}</TableBody>
          </Table>
        </Paper>
      )}
      {topProps.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Top Properties</Typography>
          <Divider sx={{ mb: 2 }} />
          <Table size="small">
            <TableHead><TableRow>{['Property', 'Revenue (€)', 'Occupancy %', 'ADR (€)'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
            <TableBody>{topProps.map((p, i) => <TableRow key={i}><TableCell>{p.name}</TableCell><TableCell>€{Number(p.revenue || 0).toFixed(2)}</TableCell><TableCell>{Number(p.occupancy || 0).toFixed(1)}%</TableCell><TableCell>€{Number(p.adr || 0).toFixed(2)}</TableCell></TableRow>)}</TableBody>
          </Table>
        </Paper>
      )}
      {yoy.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Year-over-Year Comparison</Typography>
          <Divider sx={{ mb: 2 }} />
          <Table size="small">
            <TableHead><TableRow>{['Metric', 'This Year', 'Last Year', 'Change %'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
            <TableBody>{yoy.map((r, i) => <TableRow key={i}><TableCell>{r.metric}</TableCell><TableCell>{r.this_year}</TableCell><TableCell>{r.last_year}</TableCell><TableCell><Chip size="small" label={`${r.change_pct > 0 ? '+' : ''}${r.change_pct}%`} color={r.change_pct >= 0 ? 'success' : 'error'} /></TableCell></TableRow>)}</TableBody>
          </Table>
        </Paper>
      )}
    </AppLayout>
  )
}
