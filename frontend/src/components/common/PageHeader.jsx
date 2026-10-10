import React from 'react'
import { Box, Typography } from '@mui/material'

/** Sticky ops page header for list/detail/form consistency */
export default function PageHeader({ title, subtitle, actions = null, sticky = true }) {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: { xs: 'flex-start', sm: 'center' },
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 2,
        mb: 3,
        pb: 2,
        borderBottom: '1px solid',
        borderColor: 'divider',
        ...(sticky
          ? {
              position: 'sticky',
              top: 64,
              zIndex: 2,
              bgcolor: 'background.default',
              pt: 1,
            }
          : {}),
      }}
    >
      <Box>
        <Typography variant="h5" component="h1">
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {subtitle}
          </Typography>
        )}
      </Box>
      {actions && <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>{actions}</Box>}
    </Box>
  )
}
