import React from 'react'
import { Box, Typography, Link } from '@mui/material'
import { Link as RouterLink } from 'react-router-dom'

const HERO_IMAGE =
  'https://images.unsplash.com/photo-1618773928121-c32242e63f39?auto=format&fit=crop&w=1600&q=80'

/**
 * Split atmospheric layout for auth pages — brand + place on the left, form on the right.
 */
export default function AuthShell({ title, subtitle, children }) {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', md: '1.05fr 1fr' },
      }}
    >
      <Box
        sx={{
          position: 'relative',
          display: { xs: 'none', md: 'flex' },
          flexDirection: 'column',
          justifyContent: 'flex-end',
          p: 6,
          color: 'common.white',
          backgroundImage: `linear-gradient(180deg, rgba(8,72,82,0.15) 0%, rgba(8,72,82,0.78) 70%), url(${HERO_IMAGE})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          animation: 'nepheleAuthPan 28s ease-in-out infinite alternate',
          '@keyframes nepheleAuthPan': {
            from: { backgroundPosition: '50% 40%' },
            to: { backgroundPosition: '55% 55%' },
          },
        }}
      >
        <Typography
          component={RouterLink}
          to="/landing"
          variant="h3"
          sx={{
            color: 'inherit',
            textDecoration: 'none',
            mb: 1,
            fontFamily: '"Fraunces", Georgia, serif',
          }}
        >
          Nephele
        </Typography>
        <Typography variant="h6" sx={{ maxWidth: 360, fontWeight: 400, opacity: 0.92 }}>
          Calm hospitality operations for properties by the sea.
        </Typography>
      </Box>

      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          px: { xs: 3, sm: 6, lg: 10 },
          py: 6,
          bgcolor: 'background.default',
        }}
      >
        <Box sx={{ display: { xs: 'block', md: 'none' }, mb: 4 }}>
          <Typography
            component={RouterLink}
            to="/landing"
            variant="h4"
            color="primary"
            sx={{ textDecoration: 'none', fontFamily: '"Fraunces", Georgia, serif' }}
          >
            Nephele
          </Typography>
        </Box>

        <Typography variant="h4" sx={{ mb: 1 }}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3, maxWidth: 420 }}>
            {subtitle}
          </Typography>
        )}

        <Box sx={{ maxWidth: 420, width: '100%' }}>{children}</Box>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 6 }}>
          <Link component={RouterLink} to="/landing" color="inherit" underline="hover">
            Back to home
          </Link>
        </Typography>
      </Box>
    </Box>
  )
}
