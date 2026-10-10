import React, { useState } from 'react'
import {
  Box, Paper, Typography, Chip, Table, TableHead, TableBody,
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

const DASH = '—'
const pctText = (v) => (v != null ? `${(v * 100).toFixed(0)}%` : DASH)
const pickList = (data, primaryKey) => data?.[primaryKey] || data?.results || data || []

function buildOverbookingRecs(overbooking) {
  if (Array.isArray(overbooking?.results)) return overbooking.results
  if (Array.isArray(overbooking)) return overbooking
  if (!overbooking?.recommendations) return []
  const { recommendations, property_id: propertyId, risk_distribution: risk } = overbooking
  return [{
    date: 'Current',
    property_name: propertyId ? `Property ${propertyId}` : 'All properties',
    recommended_overbooking: `${recommendations.medium_risk_allocation} / ${recommendations.high_risk_allocation}`,
    predicted_no_shows: risk?.high || 0,
    confidence: null,
  }]
}

const TABS = [
  { key: 'occupancy', label: 'Occupancy Forecast' },
  { key: 'revenue', label: 'Revenue Forecast' },
  { key: 'cancellations', label: 'Cancellation Risk' },
  { key: 'overbooking', label: 'Overbooking Recs' },
]

function ForecastTable({ headers, emptyText, children, isEmpty }) {
  return (
    <Table size="small">
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
  )
}

function ForecastPanel({ title, icon, loading, children }) {
  return (
    <Paper sx={{ p: 2 }}>
      <SectionHeader title={title} icon={icon} />
      {loading ? <LoadingSpinner /> : children}
    </Paper>
  )
}

function OccupancyRow({ f }) {
  const pct = Number(f.predicted_occupancy_rate || f.occupancy_rate || 0) * (f.predicted_occupancy_rate <= 1 ? 100 : 1)
  return (
    <TableRow>
      <TableCell>{f.forecast_date || f.date || DASH}</TableCell>
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <LinearProgress variant="determinate" value={Math.min(pct, 100)} sx={{ flex: 1, height: 8, borderRadius: 4 }} />
          <Typography variant="body2">{pct.toFixed(0)}%</Typography>
        </Box>
      </TableCell>
      <TableCell>{pctText(f.confidence_score)}</TableCell>
      <TableCell>{f.property_name || f.property || DASH}</TableCell>
    </TableRow>
  )
}

function OccupancyTab({ forecasts, loading }) {
  return (
    <ForecastPanel title="30-Day Occupancy Forecast" icon={<TrendingUp color="primary" />} loading={loading}>
      <ForecastTable headers={['Date', 'Predicted Occupancy %', 'Confidence', 'Property']} emptyText="No forecast data available." isEmpty={forecasts.length === 0}>
        {forecasts.slice(0, 30).map((f, i) => <OccupancyRow key={i} f={f} />)}
      </ForecastTable>
    </ForecastPanel>
  )
}

const money = (v) => `€${Number(v || 0).toLocaleString()}`

function RevenueTab({ forecasts, loading }) {
  return (
    <ForecastPanel title="30-Day Revenue Forecast" icon={<TrendingUp color="secondary" />} loading={loading}>
      <ForecastTable headers={['Date', 'Predicted Revenue', 'Lower Bound', 'Upper Bound', 'Property']} emptyText="No forecast data available." isEmpty={forecasts.length === 0}>
        {forecasts.slice(0, 30).map((f, i) => (
          <TableRow key={i}>
            <TableCell>{f.forecast_date || f.date || DASH}</TableCell>
            <TableCell>{money(f.predicted_revenue)}</TableCell>
            <TableCell>{money(f.lower_bound)}</TableCell>
            <TableCell>{money(f.upper_bound)}</TableCell>
            <TableCell>{f.property_name || f.property || DASH}</TableCell>
          </TableRow>
        ))}
      </ForecastTable>
    </ForecastPanel>
  )
}

function CancellationsTab({ bookings, loading }) {
  return (
    <ForecastPanel title="High-Risk Cancellations" icon={<Warning color="error" />} loading={loading}>
      {bookings.length > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {bookings.length} booking(s) identified as high cancellation risk.
        </Alert>
      )}
      <ForecastTable headers={['Booking', 'Guest', 'Check-In', 'Risk Score', 'Reason']} emptyText="No high-risk cancellations detected." isEmpty={bookings.length === 0}>
        {bookings.map((b, i) => (
          <TableRow key={i}>
            <TableCell>#{b.booking_id || b.booking || b.id}</TableCell>
            <TableCell>{b.guest_name || b.guest || DASH}</TableCell>
            <TableCell>{b.check_in_date || b.check_in || DASH}</TableCell>
            <TableCell>
              <Chip size="small" label={`${(Number(b.cancellation_probability || b.risk_score || 0) * 100).toFixed(0)}%`} color="error" />
            </TableCell>
            <TableCell>{b.risk_factors || b.reason || DASH}</TableCell>
          </TableRow>
        ))}
      </ForecastTable>
    </ForecastPanel>
  )
}

function OverbookingTab({ recs, loading }) {
  return (
    <ForecastPanel title="Overbooking Recommendations" icon={<TrendingUp color="info" />} loading={loading}>
      <ForecastTable headers={['Date', 'Property', 'Recommended Overbook', 'Predicted No-Shows', 'Confidence']} emptyText="No overbooking recommendations at this time." isEmpty={recs.length === 0}>
        {recs.map((r, i) => (
          <TableRow key={i}>
            <TableCell>{r.date || DASH}</TableCell>
            <TableCell>{r.property_name || r.property || DASH}</TableCell>
            <TableCell>{r.recommended_overbooking || r.overbook_rooms || DASH}</TableCell>
            <TableCell>{r.predicted_no_shows || DASH}</TableCell>
            <TableCell>{pctText(r.confidence)}</TableCell>
          </TableRow>
        ))}
      </ForecastTable>
    </ForecastPanel>
  )
}

function HealthChip({ health }) {
  if (!health) return null
  const healthy = health.status === 'healthy'
  return (
    <Chip
      icon={healthy ? <CheckCircle /> : <Warning />}
      label={`Model: ${health.status || 'unknown'}`}
      color={healthy ? 'success' : 'warning'}
    />
  )
}

export default function ForecastingPage() {
  const [tab, setTab] = useState('occupancy')

  const { data: occupancyData, isLoading: loadingOcc } = useGetOccupancyForecastNext30Query()
  const { data: revenueData, isLoading: loadingRev } = useGetRevenueForecastNext30Query()
  const { data: highRisk, isLoading: loadingRisk } = useGetHighRiskCancellationsQuery()
  const { data: overbooking, isLoading: loadingOver } = useGetOverbookingRecommendationsQuery()
  const { data: health } = useGetForecastHealthCheckQuery()

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">ML Forecasting & Predictions</Typography>
        <HealthChip health={health} />
      </Box>

      <Box sx={{ display: 'flex', gap: 1, mb: 3, flexWrap: 'wrap' }}>
        {TABS.map((t) => (
          <Button key={t.key} variant={tab === t.key ? 'contained' : 'outlined'} size="small" onClick={() => setTab(t.key)}>
            {t.label}
          </Button>
        ))}
      </Box>

      {tab === 'occupancy' && <OccupancyTab forecasts={pickList(occupancyData, 'forecasts')} loading={loadingOcc} />}
      {tab === 'revenue' && <RevenueTab forecasts={pickList(revenueData, 'forecasts')} loading={loadingRev} />}
      {tab === 'cancellations' && <CancellationsTab bookings={pickList(highRisk, 'predictions')} loading={loadingRisk} />}
      {tab === 'overbooking' && <OverbookingTab recs={buildOverbookingRecs(overbooking)} loading={loadingOver} />}
    </AppLayout>
  )
}
