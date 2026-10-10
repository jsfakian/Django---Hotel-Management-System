import React from 'react'
import { Box, Button, Typography } from '@mui/material'

export default function EmptyState({ title, description, actionLabel, onAction, icon = null }) {
  return (
    <Box
      sx={{
        textAlign: 'center',
        py: 8,
        px: 3,
        border: '1px dashed',
        borderColor: 'divider',
        borderRadius: 2,
        bgcolor: 'background.paper',
      }}
    >
      {icon && <Box sx={{ mb: 2, color: 'primary.main', opacity: 0.85 }}>{icon}</Box>}
      <Typography variant="h6" sx={{ mb: 1 }}>
        {title}
      </Typography>
      {description && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3, maxWidth: 420, mx: 'auto' }}>
          {description}
        </Typography>
      )}
      {actionLabel && onAction && (
        <Button variant="contained" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </Box>
  )
}
