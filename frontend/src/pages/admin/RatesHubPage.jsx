import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Typography, Grid, Paper, Button, Stack,
} from '@mui/material'
import { Category, LocalOffer, CalendarMonth, GridView } from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import PageHeader from '../../components/common/PageHeader'

const LINKS = [
  {
    title: 'Room types',
    body: 'Capacity, codes, and base pricing for each category.',
    path: '/admin/room-types',
    icon: Category,
  },
  {
    title: 'Rate plans',
    body: 'Packages, meal plans, and cancellation rules.',
    path: '/admin/rate-plans',
    icon: LocalOffer,
  },
  {
    title: 'Availability',
    body: 'Daily allotment, stop-sell, and min-stay controls.',
    path: '/admin/availability-calendar',
    icon: CalendarMonth,
  },
  {
    title: 'Inventory',
    body: 'Property-wide room availability overview.',
    path: '/admin/inventory',
    icon: GridView,
  },
]

export default function RatesHubPage() {
  const navigate = useNavigate()

  return (
    <AppLayout>
      <PageHeader
        title="Rates & availability"
        subtitle="Manage catalog, allotment, and inventory from one place."
      />
      <Grid container spacing={2} sx={{ mt: 0.5 }}>
        {LINKS.map(({ title, body, path, icon: Icon }) => (
          <Grid item xs={12} sm={6} key={path}>
            <Paper variant="outlined" sx={{ p: 2.5, height: '100%' }}>
              <Stack spacing={1.5}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Icon color="primary" />
                  <Typography variant="h6" sx={{ fontFamily: '"Fraunces", Georgia, serif' }}>
                    {title}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {body}
                </Typography>
                <Button variant="outlined" onClick={() => navigate(path)} sx={{ alignSelf: 'flex-start' }}>
                  Open
                </Button>
              </Stack>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </AppLayout>
  )
}
