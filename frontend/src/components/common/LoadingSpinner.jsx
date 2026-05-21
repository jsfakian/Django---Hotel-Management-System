import React from 'react'
import { Box, CircularProgress } from '@mui/material'

export default function LoadingSpinner({ height = '100%' }) {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height,
        width: '100%',
        minHeight: 120,
      }}
    >
      <CircularProgress />
    </Box>
  )
}
