import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, Paper, Stack, Typography } from '@mui/material'
import { ArrowForward } from '@mui/icons-material'

/**
 * Compact “today” board — one purpose per panel (arrivals or departures).
 */
export default function TodayPanel({
  title,
  count,
  pending,
  description,
  ctaLabel,
  ctaPath,
  accent = 'primary.main',
}) {
  const navigate = useNavigate()

  return (
    <Paper variant="outlined" sx={{ p: 2.5, height: '100%' }}>
      <Stack spacing={1.5}>
        <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
          <Typography variant="subtitle1" fontWeight={700}>
            {title}
          </Typography>
          <Typography
            variant="h4"
            fontWeight={700}
            sx={{ color: accent, fontVariantNumeric: 'tabular-nums' }}
          >
            {count ?? '—'}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
        {pending != null && (
          <Typography variant="caption" color="text.secondary">
            Remaining to action: <strong>{pending}</strong>
          </Typography>
        )}
        {ctaPath && (
          <Button
            size="small"
            endIcon={<ArrowForward />}
            onClick={() => navigate(ctaPath)}
            sx={{ alignSelf: 'flex-start', mt: 0.5 }}
          >
            {ctaLabel || 'Open'}
          </Button>
        )}
      </Stack>
    </Paper>
  )
}
