import React, { useState } from 'react'
import { Box, Grid, Typography, Paper, Divider, Table, TableBody, TableCell, TableHead, TableRow, LinearProgress } from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorAlert from '../../components/common/ErrorAlert'
import { AnalyticsFilters, AnalyticsHeader, KpiCard } from '../../components/analytics/AnalyticsFilters'
import { euro, pct, num, periodLabel } from '../../components/analytics/format'
import { useGetRevenueOverviewQuery } from '../../features/analytics/analyticsApi'

function Section({ title, headers, children }) {
  return (
    <Paper sx={{ p: 2, mb: 3, overflowX: 'auto' }}>
      <Typography variant="h6" gutterBottom>{title}</Typography>
      <Divider sx={{ mb: 2 }} />
      <Table size="small">
        <TableHead><TableRow>{headers.map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow></TableHead>
        <TableBody>{children}</TableBody>
      </Table>
    </Paper>
  )
}

function Bar({ value }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <LinearProgress variant="determinate" value={Math.min(num(value), 100)} sx={{ flex: 1 }} />
      <Typography variant="caption">{num(value).toFixed(1)}%</Typography>
    </Box>
  )
}

export default function RevenueAnalyticsPage() {
  const [property, setProperty] = useState('')
  const [period, setPeriod] = useState('month')
  const { data = {}, isLoading, isFetching, error } = useGetRevenueOverviewQuery({ property_id: property || undefined, period })

  const kpis = data.kpis || {}
  const bySource = data.revenue_by_source || []
  const adrTrend = data.adr_trend || []
  const byMethod = data.payments_by_method || []

  return (
    <AppLayout>
      <AnalyticsHeader title="Revenue Analytics" subtitle={periodLabel(data)}>
        <AnalyticsFilters properties={data.properties || []} property={property} onPropertyChange={setProperty} period={period} onPeriodChange={setPeriod} />
      </AnalyticsHeader>
      {error && <ErrorAlert error={error} />}
      {isLoading || isFetching ? <LoadingSpinner /> : (
        <>
          <Grid container spacing={2} sx={{ mb: 2 }}>
            {[['Room Revenue', euro(kpis.total_revenue)], ['Average Daily Rate', euro(kpis.adr, 2)], ['RevPAR', euro(kpis.revpar, 2)], ['Occupancy', pct(kpis.occupancy_rate)]].map(([label, val]) => (
              <Grid item xs={12} sm={6} md={3} key={label}><KpiCard title={label} value={val} /></Grid>
            ))}
          </Grid>
          <Grid container spacing={2} sx={{ mb: 4 }}>
            {[['Payments collected', kpis.collected, 'Completed payments in period'], ['Outstanding', kpis.outstanding, 'Pending payments'], ['Refunded', kpis.refunded, 'Refunds issued']].map(([label, val, caption]) => (
              <Grid item xs={12} sm={4} key={label}><KpiCard title={label} value={euro(val)} caption={caption} /></Grid>
            ))}
          </Grid>
          {bySource.length > 0 && (
            <Section title="Revenue by Source" headers={['Source', 'Room revenue', '% of Total', 'Bookings']}>
              {bySource.map((s) => (
                <TableRow key={s.source}>
                  <TableCell>{s.label || s.source}</TableCell>
                  <TableCell>{euro(s.revenue, 2)}</TableCell>
                  <TableCell sx={{ width: 220 }}><Bar value={s.pct} /></TableCell>
                  <TableCell>{s.bookings}</TableCell>
                </TableRow>
              ))}
            </Section>
          )}
          {byMethod.length > 0 && (
            <Section title="Payments by Method" headers={['Method', 'Payments', 'Amount']}>
              {byMethod.map((m) => (
                <TableRow key={m.method}><TableCell>{m.method}</TableCell><TableCell>{m.count}</TableCell><TableCell>{euro(m.amount, 2)}</TableCell></TableRow>
              ))}
            </Section>
          )}
          {adrTrend.length > 0 && (
            <Section title="ADR Trend" headers={['Date', 'ADR', 'Occupancy', 'Room revenue']}>
              {[...adrTrend].reverse().map((r) => (
                <TableRow key={r.date}><TableCell>{r.date}</TableCell><TableCell>{euro(r.adr, 2)}</TableCell><TableCell>{pct(r.occupancy)}</TableCell><TableCell>{euro(r.revenue, 2)}</TableCell></TableRow>
              ))}
            </Section>
          )}
        </>
      )}
    </AppLayout>
  )
}
