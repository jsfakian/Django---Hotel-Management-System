import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Grid, Card, CardContent, CardActionArea, Typography, Box } from '@mui/material'
import { TrendingUp, SettingsInputComponent, AttachMoney, People, PriceChange, Assessment } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'

const DASHBOARDS = [
  { title: 'Executive Dashboard', desc: 'Revenue trends, occupancy, ADR, year-over-year KPIs', icon: <TrendingUp sx={{ fontSize: 48, color: 'primary.main' }} />, path: '/analytics/executive' },
  { title: 'Operational Dashboard', desc: 'Real-time room status, check-ins/outs, staff tasks', icon: <SettingsInputComponent sx={{ fontSize: 48, color: 'secondary.main' }} />, path: '/analytics/operational' },
  { title: 'Revenue Analytics', desc: 'Revenue by source, ADR trends, discount impact', icon: <AttachMoney sx={{ fontSize: 48, color: 'success.main' }} />, path: '/analytics/revenue' },
  { title: 'Guest Analytics', desc: 'Demographics, booking patterns, satisfaction scores', icon: <People sx={{ fontSize: 48, color: 'info.main' }} />, path: '/analytics/guest' },
  { title: 'Forecasting', desc: 'Occupancy/revenue forecasts and cancellation/no-show risk', icon: <TrendingUp sx={{ fontSize: 48, color: 'error.main' }} />, path: '/analytics/forecasting' },
  { title: 'Custom Reports', desc: 'Build and schedule reports with execution tracking', icon: <Assessment sx={{ fontSize: 48, color: 'secondary.main' }} />, path: '/analytics/reports' },
  { title: 'Pricing Analysis', desc: 'Dynamic pricing recommendations and ML model insights', icon: <PriceChange sx={{ fontSize: 48, color: 'warning.main' }} />, path: '/admin/pricing' },
]

export default function AnalyticsHubPage() {
  const navigate = useNavigate()

  return (
    <AppLayout>
      <Typography variant="h4" sx={{ mb: 1 }}>Analytics</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>Select a dashboard to view detailed insights.</Typography>
      <Grid container spacing={3}>
        {DASHBOARDS.map(({ title, desc, icon, path }) => (
          <Grid item xs={12} sm={6} md={4} key={title}>
            <Card sx={{ height: '100%' }}>
              <CardActionArea sx={{ height: '100%', p: 1 }} onClick={() => navigate(path)}>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Box sx={{ mb: 2 }}>{icon}</Box>
                  <Typography variant="h6" gutterBottom>{title}</Typography>
                  <Typography variant="body2" color="text.secondary">{desc}</Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </AppLayout>
  )
}
