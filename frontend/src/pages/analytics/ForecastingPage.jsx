import React, { useState } from 'react'
import {
  Box, Paper, Typography, Chip, Table, TableHead, TableBody,
  TableRow, TableCell, Button, LinearProgress, Alert, Tooltip,
} from '@mui/material'
import { Warning, CheckCircle, TrendingUp, Error as ErrorIcon } from '@mui/icons-material'
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
const num = (v) => Number(v || 0)
const pickList = (data, primaryKey) => data?.[primaryKey] || data?.results || (Array.isArray(data) ? data : [])
const humanise = (key) => key.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())

function buildOverbookingRecs(overbooking) {
  if (Array.isArray(overbooking?.results)) return overbooking.results
  if (Array.isArray(overbooking)) return overbooking
  if (!overbooking?.recommendations) return []
  const { recommendations, property_id: propertyId, risk_distribution: risk, total_bookings: total } = overbooking
  return [{
    date: 'Upcoming arrivals',
    property_name: propertyId ? `Property ${propertyId}` : 'All properties',
    recommended_overbooking: `${recommendations.medium_risk_allocation} / ${recommendations.high_risk_allocation}`,
    predicted_no_shows: risk?.high || 0,
    analysed: total,
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
    <Box sx={{ overflowX: 'auto' }}>
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
    </Box>
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
  const value = num(f.predicted_occupancy)
  return (
    <TableRow>
      <TableCell>{f.target_date || DASH}</TableCell>
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 160 }}>
          <LinearProgress variant="determinate" value={Math.min(value, 100)} sx={{ flex: 1, height: 8, borderRadius: 4 }} />
          <Typography variant="body2">{value.toFixed(0)}%</Typography>
        </Box>
      </TableCell>
      <TableCell>{f.lower_bound != null ? `${num(f.lower_bound).toFixed(0)}–${num(f.upper_bound).toFixed(0)}%` : DASH}</TableCell>
      <TableCell>{f.property_name || f.property || DASH}</TableCell>
    </TableRow>
  )
}

function OccupancyTab({ forecasts, loading }) {
  return (
    <ForecastPanel title="30-Day Occupancy Forecast" icon={<TrendingUp color="primary" />} loading={loading}>
      <ForecastTable headers={['Date', 'Predicted Occupancy', 'Range', 'Property']} emptyText="No forecast data available." isEmpty={forecasts.length === 0}>
        {forecasts.map((f) => <OccupancyRow key={f.id} f={f} />)}
      </ForecastTable>
    </ForecastPanel>
  )
}

const money = (v) => `€${num(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}`

function RevenueTab({ forecasts, loading }) {
  return (
    <ForecastPanel title="30-Day Revenue Forecast" icon={<TrendingUp color="secondary" />} loading={loading}>
      <ForecastTable headers={['Date', 'Predicted Revenue', 'Lower Bound', 'Upper Bound', 'Occupancy', 'Property']} emptyText="No forecast data available." isEmpty={forecasts.length === 0}>
        {forecasts.map((f) => (
          <TableRow key={f.id}>
            <TableCell>{f.target_date || DASH}</TableCell>
            <TableCell>{money(f.predicted_revenue)}</TableCell>
            <TableCell>{money(f.lower_bound)}</TableCell>
            <TableCell>{money(f.upper_bound)}</TableCell>
            <TableCell>{f.predicted_occupancy != null ? `${num(f.predicted_occupancy).toFixed(0)}%` : DASH}</TableCell>
            <TableCell>{f.property_name || f.property || DASH}</TableCell>
          </TableRow>
        ))}
      </ForecastTable>
    </ForecastPanel>
  )
}

function RiskFactors({ factors }) {
  const active = factors && typeof factors === 'object' ? Object.entries(factors).filter(([, v]) => v).map(([k]) => k) : []
  if (!active.length) return DASH
  return (
    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
      {active.map((k) => <Chip key={k} size="small" variant="outlined" label={humanise(k)} />)}
    </Box>
  )
}

function CancellationsTab({ bookings, total, loading }) {
  return (
    <ForecastPanel title="High-Risk Cancellations" icon={<Warning color="error" />} loading={loading}>
      {total > 0 && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {total} upcoming booking(s) identified as high cancellation risk{total > bookings.length ? ` (showing top ${bookings.length})` : ''}.
        </Alert>
      )}
      <ForecastTable headers={['Booking', 'Guest', 'Check-In', 'Room', 'Property', 'Risk', 'Reasons']} emptyText="No high-risk cancellations detected." isEmpty={bookings.length === 0}>
        {bookings.map((b) => (
          <TableRow key={b.id}>
            <TableCell>#{b.booking_id || DASH}</TableCell>
            <TableCell>{b.guest_name || DASH}</TableCell>
            <TableCell>{b.check_in_date || DASH}</TableCell>
            <TableCell>{b.room_number || DASH}</TableCell>
            <TableCell>{b.property_name || DASH}</TableCell>
            <TableCell><Chip size="small" label={`${(num(b.cancellation_risk_score) * 100).toFixed(0)}%`} color="error" /></TableCell>
            <TableCell><RiskFactors factors={b.risk_factors} /></TableCell>
          </TableRow>
        ))}
      </ForecastTable>
    </ForecastPanel>
  )
}

function OverbookingTab({ recs, loading }) {
  return (
    <ForecastPanel title="Overbooking Recommendations" icon={<TrendingUp color="info" />} loading={loading}>
      <ForecastTable headers={['Scope', 'Property', 'Recommended Allocation (medium / high risk)', 'High No-Show Risk Bookings', 'Bookings Analysed']} emptyText="No overbooking recommendations at this time." isEmpty={recs.length === 0}>
        {recs.map((r, i) => (
          <TableRow key={i}>
            <TableCell>{r.date || DASH}</TableCell>
            <TableCell>{r.property_name || r.property || DASH}</TableCell>
            <TableCell>{r.recommended_overbooking || r.overbook_rooms || DASH}</TableCell>
            <TableCell>{r.predicted_no_shows ?? DASH}</TableCell>
            <TableCell>{r.analysed ?? DASH}</TableCell>
          </TableRow>
        ))}
      </ForecastTable>
    </ForecastPanel>
  )
}

const HEALTH = {
  green: { label: 'Models healthy', color: 'success', icon: <CheckCircle /> },
  yellow: { label: 'Models need review', color: 'warning', icon: <Warning /> },
  red: { label: 'Retraining required', color: 'error', icon: <ErrorIcon /> },
}

function HealthChip({ health }) {
  if (!health?.health_status) return null
  const cfg = HEALTH[health.health_status] || { label: health.health_status, color: 'default', icon: <Warning /> }
  return (
    <Tooltip title={health.action_required || ''}>
      <Chip icon={cfg.icon} label={cfg.label} color={cfg.color} />
    </Tooltip>
  )
}

export default function ForecastingPage() {
  const [tab, setTab] = useState('occupancy')

  const { data: occupancyData, isLoading: loadingOcc } = useGetOccupancyForecastNext30Query()
  const { data: revenueData, isLoading: loadingRev } = useGetRevenueForecastNext30Query()
  const { data: highRisk, isLoading: loadingRisk } = useGetHighRiskCancellationsQuery()
  const { data: overbooking, isLoading: loadingOver } = useGetOverbookingRecommendationsQuery()
  const { data: health } = useGetForecastHealthCheckQuery()

  const riskList = pickList(highRisk, 'predictions')

  return (
    <AppLayout>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, gap: 2, flexWrap: 'wrap' }}>
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
      {tab === 'cancellations' && <CancellationsTab bookings={riskList} total={highRisk?.high_risk_count ?? riskList.length} loading={loadingRisk} />}
      {tab === 'overbooking' && <OverbookingTab recs={buildOverbookingRecs(overbooking)} loading={loadingOver} />}
    </AppLayout>
  )
}
