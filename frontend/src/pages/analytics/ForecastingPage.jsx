import React, { useState } from 'react'
import {
  Box, Paper, Typography, Grid, Chip, Table, TableHead, TableBody,
  TableRow, TableCell, Button, LinearProgress, Alert,
} from '@mui/material'
import { Warning, CheckCircle, TrendingUp } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import {
  useGetOccupancyForecastNext30Query,
  useGetRevenueForecastNext30Query,
  useGetHighRiskCancellationsQuery,
  useGetOverbookingRecommendationsQuery,
  useGetForecastHealthCheckQuery,
} from '../../features/analytics/analyticsApi'

function SectionHeader({ title, icon }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
      {icon}
      <Typography variant="h6">{title}</Typography>
    </Box>
  )
}

export default function ForecastingPage() {
  const [tab, setTab] = useState('occupancy')

  const { data: occupancyData, isLoading: loadingOcc } = useGetOccupancyForecastNext30Query()
  const { data: revenueData, isLoading: loadingRev } = useGetRevenueForecastNext30Query()
  const { data: highRisk, isLoading: loadingRisk } = useGetHighRiskCancellationsQuery()
  const { data: overbooking, isLoading: loadingOver } = useGetOverbookingRecommendationsQuery()
  const { data: health } = useGetForecastHealthCheckQuery()

  const occupancyForecasts = occupancyData?.forecasts || occupancyData?.results || occupancyData || []
  const revenueForecasts = revenueData?.forecasts || revenueData?.results || revenueData || []
  const riskBookings = highRisk?.predictions || highRisk?.results || highRisk || []
  const overbookingRecs = Array.isArray(overbooking?.results)
    ? overbooking.results
    : Array.isArray(overbooking)
      ? overbooking
      : overbooking?.recommendations
        ? [{
            date: 'Current',
            property_name: overbooking.property_id ? `Property ${overbooking.property_id}` : 'All properties',
            recommended_overbooking: `${overbooking.recommendations.medium_risk_allocation} / ${overbooking.recommendations.high_risk_allocation}`,
            predicted_no_shows: overbooking.risk_distribution?.high || 0,
            confidence: null,
          }]
        : []

  const TABS = [
    { key: 'occupancy', label: 'Occupancy Forecast' },
    { key: 'revenue', label: 'Revenue Forecast' },
    { key: 'cancellations', label: 'Cancellation Risk' },
    { key: 'overbooking', label: 'Overbooking Recs' },
  ]

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">ML Forecasting & Predictions</Typography>
        {health && (
          <Chip
            icon={health.status === 'healthy' ? <CheckCircle /> : <Warning />}
            label={`Model: ${health.status || 'unknown'}`}
            color={health.status === 'healthy' ? 'success' : 'warning'}
          />
        )}
      </Box>

      <Box sx={{ display: 'flex', gap: 1, mb: 3, flexWrap: 'wrap' }}>
        {TABS.map((t) => (
          <Button key={t.key} variant={tab === t.key ? 'contained' : 'outlined'} size="small" onClick={() => setTab(t.key)}>
            {t.label}
          </Button>
        ))}
      </Box>

      {/* Occupancy Forecast */}
      {tab === 'occupancy' && (
        <Paper sx={{ p: 2 }}>
          <SectionHeader title="30-Day Occupancy Forecast" icon={<TrendingUp color="primary" />} />
          {loadingOcc ? <LoadingSpinner /> : (
            <Table size="small">
              <TableHead>
                <TableRow>{['Date', 'Predicted Occupancy %', 'Confidence', 'Property'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow>
              </TableHead>
              <TableBody>
                {occupancyForecasts.length === 0 && (
                  <TableRow><TableCell colSpan={4}><Typography color="text.secondary">No forecast data available.</Typography></TableCell></TableRow>
                )}
                {occupancyForecasts.slice(0, 30).map((f, i) => {
                  const pct = Number(f.predicted_occupancy_rate || f.occupancy_rate || 0) * (f.predicted_occupancy_rate <= 1 ? 100 : 1)
                  return (
                    <TableRow key={i}>
                      <TableCell>{f.forecast_date || f.date || '—'}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LinearProgress variant="determinate" value={Math.min(pct, 100)} sx={{ flex: 1, height: 8, borderRadius: 4 }} />
                          <Typography variant="body2">{pct.toFixed(0)}%</Typography>
                        </Box>
                      </TableCell>
                      <TableCell>{f.confidence_score != null ? `${(f.confidence_score * 100).toFixed(0)}%` : '—'}</TableCell>
                      <TableCell>{f.property_name || f.property || '—'}</TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </Paper>
      )}

      {/* Revenue Forecast */}
      {tab === 'revenue' && (
        <Paper sx={{ p: 2 }}>
          <SectionHeader title="30-Day Revenue Forecast" icon={<TrendingUp color="secondary" />} />
          {loadingRev ? <LoadingSpinner /> : (
            <Table size="small">
              <TableHead>
                <TableRow>{['Date', 'Predicted Revenue', 'Lower Bound', 'Upper Bound', 'Property'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow>
              </TableHead>
              <TableBody>
                {revenueForecasts.length === 0 && (
                  <TableRow><TableCell colSpan={5}><Typography color="text.secondary">No forecast data available.</Typography></TableCell></TableRow>
                )}
                {revenueForecasts.slice(0, 30).map((f, i) => (
                  <TableRow key={i}>
                    <TableCell>{f.forecast_date || f.date || '—'}</TableCell>
                    <TableCell>€{Number(f.predicted_revenue || 0).toLocaleString()}</TableCell>
                    <TableCell>€{Number(f.lower_bound || 0).toLocaleString()}</TableCell>
                    <TableCell>€{Number(f.upper_bound || 0).toLocaleString()}</TableCell>
                    <TableCell>{f.property_name || f.property || '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Paper>
      )}

      {/* Cancellation Risk */}
      {tab === 'cancellations' && (
        <Paper sx={{ p: 2 }}>
          <SectionHeader title="High-Risk Cancellations" icon={<Warning color="error" />} />
          {loadingRisk ? <LoadingSpinner /> : (
            <>
              {riskBookings.length > 0 && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  {riskBookings.length} booking(s) identified as high cancellation risk.
                </Alert>
              )}
              <Table size="small">
                <TableHead>
                  <TableRow>{['Booking', 'Guest', 'Check-In', 'Risk Score', 'Reason'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow>
                </TableHead>
                <TableBody>
                  {riskBookings.length === 0 && (
                    <TableRow><TableCell colSpan={5}><Typography color="text.secondary">No high-risk cancellations detected.</Typography></TableCell></TableRow>
                  )}
                  {riskBookings.map((b, i) => (
                    <TableRow key={i}>
                      <TableCell>#{b.booking_id || b.booking || b.id}</TableCell>
                      <TableCell>{b.guest_name || b.guest || '—'}</TableCell>
                      <TableCell>{b.check_in_date || b.check_in || '—'}</TableCell>
                      <TableCell>
                        <Chip size="small" label={`${(Number(b.cancellation_probability || b.risk_score || 0) * 100).toFixed(0)}%`} color="error" />
                      </TableCell>
                      <TableCell>{b.risk_factors || b.reason || '—'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </>
          )}
        </Paper>
      )}

      {/* Overbooking Recommendations */}
      {tab === 'overbooking' && (
        <Paper sx={{ p: 2 }}>
          <SectionHeader title="Overbooking Recommendations" icon={<TrendingUp color="info" />} />
          {loadingOver ? <LoadingSpinner /> : (
            <Table size="small">
              <TableHead>
                <TableRow>{['Date', 'Property', 'Recommended Overbook', 'Predicted No-Shows', 'Confidence'].map((h) => <TableCell key={h}>{h}</TableCell>)}</TableRow>
              </TableHead>
              <TableBody>
                {overbookingRecs.length === 0 && (
                  <TableRow><TableCell colSpan={5}><Typography color="text.secondary">No overbooking recommendations at this time.</Typography></TableCell></TableRow>
                )}
                {overbookingRecs.map((r, i) => (
                  <TableRow key={i}>
                    <TableCell>{r.date || '—'}</TableCell>
                    <TableCell>{r.property_name || r.property || '—'}</TableCell>
                    <TableCell>{r.recommended_overbooking || r.overbook_rooms || '—'}</TableCell>
                    <TableCell>{r.predicted_no_shows || '—'}</TableCell>
                    <TableCell>{r.confidence != null ? `${(r.confidence * 100).toFixed(0)}%` : '—'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Paper>
      )}
    </AppLayout>
  )
}
