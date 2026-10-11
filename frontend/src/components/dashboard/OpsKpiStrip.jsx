import React from 'react'
import { Box, Grid, Paper, Typography } from '@mui/material'

function KpiTile({ label, value, hint, icon: Icon, accent = 'primary.main' }) {
  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        height: '100%',
        display: 'flex',
        alignItems: 'flex-start',
        gap: 1.5,
        borderLeft: 3,
        borderLeftColor: accent,
      }}
    >
      {Icon ? (
        <Box
          sx={{
            width: 40,
            height: 40,
            borderRadius: 1.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: 'action.hover',
            flexShrink: 0,
          }}
        >
          <Icon sx={{ color: accent, fontSize: 22 }} />
        </Box>
      ) : null}
      <Box sx={{ minWidth: 0 }}>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
          {label}
        </Typography>
        <Typography variant="h5" fontWeight={700} sx={{ lineHeight: 1.2, fontVariantNumeric: 'tabular-nums' }}>
          {value ?? '—'}
        </Typography>
        {hint ? (
          <Typography variant="caption" color="text.secondary">
            {hint}
          </Typography>
        ) : null}
      </Box>
    </Paper>
  )
}

/** Horizontal KPI strip inspired by Cloudbeds / OPERA day tiles. */
export default function OpsKpiStrip({ items = [] }) {
  if (!items.length) return null
  const md = items.length >= 6 ? 2 : items.length >= 4 ? 3 : 4

  return (
    <Grid container spacing={1.5}>
      {items.map((item) => (
        <Grid item xs={6} sm={4} md={md} key={item.label}>
          <KpiTile {...item} />
        </Grid>
      ))}
    </Grid>
  )
}
