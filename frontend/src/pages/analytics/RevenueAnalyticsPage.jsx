import React, { useState } from 'react'
import { Box, Grid, Card, CardContent, Typography, FormControl, InputLabel, Select, MenuItem, Paper, Divider, Table, TableBody, TableCell, TableHead, TableRow, LinearProgress } from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetRevenueAnalyticsQuery } from '../../features/analytics/analyticsApi'

export default function RevenueAnalyticsPage() {
  const [period, setPeriod] = useState('month')
  const { data, isLoading, error } = useGetRevenueAnalyticsQuery({ period })

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>

  const kpis = data?.kpis || {}
  const bySource = data?.revenue_by_source || []
  const adrTrend = data?.adr_trend || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">Revenue Analytics</Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Period</InputLabel>
          <Select value={period} label="Period" onChange={(e) => setPeriod(e.target.value)}>
            {['day', 'week', 'month', 'year'].map((p) => <MenuItem key={p} value={p}>{p}</MenuItem>)}
          </Select>
        </FormControl>
      </Box>
      {error && <ErrorAlert error={error} />}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {[['Total Revenue', `€${Number(kpis.total_revenue || 0).toLocaleString()}`], ['Average Daily Rate', `€${Number(kpis.adr || 0).toFixed(2)}`], ['RevPAR', `€${Number(kpis.revpar || 0).toFixed(2)}`]].map(([label, val]) => (
          <Grid item xs={12} sm={4} key={label}>
            <Card><CardContent><Typography variant="body2" color="text.secondary">{label}</Typography><Typography variant="h4" fontWeight={700}>{val}</Typography></CardContent></Card>
          </Grid>
        ))}
      </Grid>
      {bySource.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Revenue by Source</Typography>
          <Divider sx={{ mb: 2 }} />
          <Table size="small">
            <TableHead><TableRow>{['Source', 'Revenue (€)', '% of Total', 'Bookings'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
            <TableBody>{bySource.map((s, i) => (
              <TableRow key={i}>
                <TableCell>{s.source}</TableCell>
                <TableCell>€{Number(s.revenue || 0).toFixed(2)}</TableCell>
                <TableCell sx={{ width: 200 }}><Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><LinearProgress variant="determinate" value={s.pct || 0} sx={{ flex: 1 }} /><Typography variant="caption">{s.pct || 0}%</Typography></Box></TableCell>
                <TableCell>{s.bookings}</TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </Paper>
      )}
      {adrTrend.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>ADR Trend</Typography>
          <Divider sx={{ mb: 2 }} />
          <Table size="small">
            <TableHead><TableRow>{['Date', 'ADR (€)', 'Occupancy %', 'Revenue (€)'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
            <TableBody>{adrTrend.map((r, i) => <TableRow key={i}><TableCell>{r.date}</TableCell><TableCell>€{Number(r.adr || 0).toFixed(2)}</TableCell><TableCell>{Number(r.occupancy || 0).toFixed(1)}%</TableCell><TableCell>€{Number(r.revenue || 0).toFixed(2)}</TableCell></TableRow>)}</TableBody>
          </Table>
        </Paper>
      )}
    </AppLayout>
  )
}
