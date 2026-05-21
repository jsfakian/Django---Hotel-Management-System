import React, { useState } from 'react'
import { Box, Grid, Card, CardContent, Typography, FormControl, InputLabel, Select, MenuItem, Paper, Divider, Table, TableBody, TableCell, TableHead, TableRow, LinearProgress } from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import { useGetGuestAnalyticsQuery } from '../../features/analytics/analyticsApi'

export default function GuestAnalyticsPage() {
  const [period, setPeriod] = useState('month')
  const { data, isLoading, error } = useGetGuestAnalyticsQuery({ period })

  if (isLoading) return <AppLayout><LoadingSpinner /></AppLayout>

  const kpis = data?.kpis || {}
  const segments = data?.guest_segments || []
  const sources = data?.booking_sources || []
  const nationalities = data?.nationalities || []

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">Guest Analytics</Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Period</InputLabel>
          <Select value={period} label="Period" onChange={(e) => setPeriod(e.target.value)}>
            {['day', 'week', 'month', 'year'].map((p) => <MenuItem key={p} value={p}>{p}</MenuItem>)}
          </Select>
        </FormControl>
      </Box>
      {error && <ErrorAlert error={error} />}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {[['Total Guests', kpis.total_guests], ['Repeat Guests', `${Number(kpis.repeat_rate || 0).toFixed(1)}%`], ['Avg Stay Length', `${Number(kpis.avg_stay || 0).toFixed(1)} nights`]].map(([label, val]) => (
          <Grid item xs={12} sm={4} key={label}>
            <Card><CardContent><Typography variant="body2" color="text.secondary">{label}</Typography><Typography variant="h4" fontWeight={700}>{val || '—'}</Typography></CardContent></Card>
          </Grid>
        ))}
      </Grid>
      {segments.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Guest Segmentation</Typography>
          <Divider sx={{ mb: 2 }} />
          <Table size="small">
            <TableHead><TableRow>{['Segment', 'Count', 'Revenue (€)', 'Avg Stay'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
            <TableBody>{segments.map((s, i) => <TableRow key={i}><TableCell>{s.segment}</TableCell><TableCell>{s.count}</TableCell><TableCell>€{Number(s.revenue || 0).toFixed(2)}</TableCell><TableCell>{Number(s.avg_stay || 0).toFixed(1)} nights</TableCell></TableRow>)}</TableBody>
          </Table>
        </Paper>
      )}
      {nationalities.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>Nationality Distribution</Typography>
          <Divider sx={{ mb: 2 }} />
          <Table size="small">
            <TableHead><TableRow>{['Country', 'Guests', '% of Total'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
            <TableBody>{nationalities.map((n, i) => (
              <TableRow key={i}>
                <TableCell>{n.country}</TableCell>
                <TableCell>{n.guests}</TableCell>
                <TableCell sx={{ width: 200 }}><Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><LinearProgress variant="determinate" value={n.pct || 0} sx={{ flex: 1 }} /><Typography variant="caption">{n.pct || 0}%</Typography></Box></TableCell>
              </TableRow>
            ))}</TableBody>
          </Table>
        </Paper>
      )}
    </AppLayout>
  )
}
