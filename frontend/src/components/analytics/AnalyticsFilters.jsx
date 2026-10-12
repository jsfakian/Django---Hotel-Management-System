import React from 'react'
import { Box, Card, CardContent, FormControl, InputLabel, MenuItem, Select, Typography } from '@mui/material'
import { TrendingDown, TrendingUp } from '@mui/icons-material'
import { PERIODS } from './format'

/** Property + period selectors shared by the analytics pages. */
export function AnalyticsFilters({ properties = [], property, onPropertyChange, period, onPeriodChange }) {
  return (
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
      {onPropertyChange && (
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Property</InputLabel>
          <Select value={property} label="Property" onChange={(e) => onPropertyChange(e.target.value)}>
            <MenuItem value="">All properties</MenuItem>
            {properties.map((p) => <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>)}
          </Select>
        </FormControl>
      )}
      {onPeriodChange && (
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Period</InputLabel>
          <Select value={period} label="Period" onChange={(e) => onPeriodChange(e.target.value)}>
            {PERIODS.map(([value, label]) => <MenuItem key={value} value={value}>{label}</MenuItem>)}
          </Select>
        </FormControl>
      )}
    </Box>
  )
}

export function AnalyticsHeader({ title, subtitle, children }) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, flexDirection: { xs: 'column', sm: 'row' }, gap: 2, mb: 3 }}>
      <Box>
        <Typography variant="h5">{title}</Typography>
        {subtitle && <Typography variant="body2" color="text.secondary">{subtitle}</Typography>}
      </Box>
      {children}
    </Box>
  )
}

/** KPI tile; ``trend`` is a % change vs the previous period (null hides the arrow). */
export function KpiCard({ title, value, trend, caption }) {
  const hasTrend = trend !== undefined && trend !== null
  const isUp = hasTrend && trend >= 0
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="body2" color="text.secondary">{title}</Typography>
        <Typography variant="h4" fontWeight={700} sx={{ my: 1 }}>{value}</Typography>
        {hasTrend && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {isUp ? <TrendingUp color="success" fontSize="small" /> : <TrendingDown color="error" fontSize="small" />}
            <Typography variant="body2" color={isUp ? 'success.main' : 'error.main'}>
              {Math.abs(trend).toFixed(1)}% vs previous period
            </Typography>
          </Box>
        )}
        {caption && <Typography variant="caption" color="text.secondary">{caption}</Typography>}
      </CardContent>
    </Card>
  )
}
