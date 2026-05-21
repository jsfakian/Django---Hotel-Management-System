import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Typography, Button } from '@mui/material'
import { SentimentDissatisfied, Home } from '@mui/icons-material'

export default function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'background.default',
        textAlign: 'center',
        p: 3,
      }}
    >
      <SentimentDissatisfied sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
      <Typography variant="h2" fontWeight={700} color="text.primary">
        404
      </Typography>
      <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
        Page not found
      </Typography>
      <Typography variant="body2" color="text.disabled" sx={{ mb: 3 }}>
        The page you are looking for does not exist or has been moved.
      </Typography>
      <Button
        variant="contained"
        startIcon={<Home />}
        onClick={() => navigate('/')}
      >
        Back to Home
      </Button>
    </Box>
  )
}
