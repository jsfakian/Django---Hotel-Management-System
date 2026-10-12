import React, { useState } from 'react'
import { Box, Grid, Typography, Paper, Divider, Table, TableBody, TableCell, TableHead, TableRow, LinearProgress } from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import { AnalyticsFilters, AnalyticsHeader, KpiCard } from '../../components/analytics/AnalyticsFilters'
import { euro, pct, num, periodLabel } from '../../components/analytics/format'
import { useGetGuestOverviewQuery } from '../../features/analytics/analyticsApi'

export default function GuestAnalyticsPage() {
  const [property, setProperty] = useState('')
  const [period, setPeriod] = useState('month')
  const { data = {}, isLoading, isFetching, error } = useGetGuestOverviewQuery({ property_id: property || undefined, period })

  const kpis = data.kpis || {}
  const segments = data.guest_segments || []
  const nationalities = data.nationalities || []
  const tiles = [
    ['Guests', num(kpis.total_guests).toLocaleString(), `${num(kpis.new_guests)} new · ${num(kpis.repeat_guests)} returning`],
    ['Repeat Guest Rate', pct(kpis.repeat_rate), 'Guests with an earlier stay'],
    ['Avg Length of Stay', `${num(kpis.avg_stay).toFixed(1)} nights`],
    ['Avg Booking Lead Time', `${num(kpis.avg_lead_time).toFixed(0)} days`, `${num(kpis.in_house)} guests in house now`],
  ]

  return (
    <AppLayout>
      <AnalyticsHeader title="Guest Analytics" subtitle={periodLabel(data)}>
        <AnalyticsFilters properties={data.properties || []} property={property} onPropertyChange={setProperty} period={period} onPeriodChange={setPeriod} />
      </AnalyticsHeader>
      {error && <ErrorAlert error={error} />}
      {isLoading || isFetching ? <LoadingSpinner /> : (
        <>
          <Grid container spacing={2} sx={{ mb: 4 }}>
            {tiles.map(([label, val, caption]) => (
              <Grid item xs={12} sm={6} md={3} key={label}><KpiCard title={label} value={val} caption={caption} /></Grid>
            ))}
          </Grid>
          {segments.length > 0 && (
            <Paper sx={{ p: 2, mb: 3, overflowX: 'auto' }}>
              <Typography variant="h6" gutterBottom>Guest Segmentation</Typography>
              <Divider sx={{ mb: 2 }} />
              <Table size="small">
                <TableHead><TableRow>{['Segment', 'Stays', 'Room revenue', 'Avg Stay'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
                <TableBody>{segments.map((s) => <TableRow key={s.segment}><TableCell>{s.segment}</TableCell><TableCell>{s.count}</TableCell><TableCell>{euro(s.revenue, 2)}</TableCell><TableCell>{num(s.avg_stay).toFixed(1)} nights</TableCell></TableRow>)}</TableBody>
              </Table>
            </Paper>
          )}
          {nationalities.length > 0 && (
            <Paper sx={{ p: 2, overflowX: 'auto' }}>
              <Typography variant="h6" gutterBottom>Guest Origin</Typography>
              <Divider sx={{ mb: 2 }} />
              <Table size="small">
                <TableHead><TableRow>{['Country', 'Guests', '% of Total'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
                <TableBody>{nationalities.map((n) => (
                  <TableRow key={n.country}>
                    <TableCell>{n.country}</TableCell>
                    <TableCell>{n.guests}</TableCell>
                    <TableCell sx={{ width: 220 }}><Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><LinearProgress variant="determinate" value={Math.min(num(n.pct), 100)} sx={{ flex: 1 }} /><Typography variant="caption">{num(n.pct).toFixed(1)}%</Typography></Box></TableCell>
                  </TableRow>
                ))}</TableBody>
              </Table>
            </Paper>
          )}
        </>
      )}
    </AppLayout>
  )
}
