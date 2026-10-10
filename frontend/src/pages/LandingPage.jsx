import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, Typography } from '@mui/material'

const HERO_IMAGE =
  'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=2000&q=80'

const OUTLINE_SX = { borderColor: 'rgba(255,255,255,0.55)', color: 'common.white' }

function LandingHeader({ isLoggedIn, navigate }) {
  return (
    <Box
      component="header"
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        px: { xs: 3, md: 6 },
        py: 3,
        animation: 'nepheleFadeUp 0.8s ease-out 0.15s both',
        '@keyframes nepheleFadeUp': {
          from: { opacity: 0, transform: 'translateY(12px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
      }}
    >
      <Typography
        variant="h4"
        sx={{
          fontFamily: '"Fraunces", Georgia, serif',
          fontWeight: 600,
          letterSpacing: '-0.02em',
        }}
      >
        Nephele
      </Typography>
      <Button
        color="inherit"
        variant="outlined"
        onClick={() => navigate(isLoggedIn ? '/' : '/login')}
        sx={OUTLINE_SX}
      >
        {isLoggedIn ? 'Go to Dashboard' : 'Sign In'}
      </Button>
    </Box>
  )
}

function HeroActions({ isLoggedIn, navigate }) {
  return (
    <Box
      sx={{
        display: 'flex',
        gap: 2,
        flexWrap: 'wrap',
        animation: 'nepheleFadeUp 0.9s ease-out 0.55s both',
      }}
    >
      {isLoggedIn ? (
        <Button size="large" variant="contained" color="secondary" onClick={() => navigate('/')}>
          Open dashboard
        </Button>
      ) : (
        <>
          <Button size="large" variant="contained" color="secondary" onClick={() => navigate('/login')}>
            Sign in
          </Button>
          <Button
            size="large"
            variant="outlined"
            onClick={() => navigate('/register')}
            sx={{
              color: 'common.white',
              borderColor: 'rgba(255,255,255,0.7)',
              '&:hover': {
                borderColor: 'common.white',
                bgcolor: 'rgba(255,255,255,0.08)',
              },
            }}
          >
            Create guest account
          </Button>
        </>
      )}
    </Box>
  )
}

function HeroCopy({ isLoggedIn, navigate }) {
  return (
    <Box
      sx={{
        minHeight: { xs: 'calc(100vh - 96px)', md: 'calc(100vh - 88px)' },
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-end',
        px: { xs: 3, md: 6 },
        pb: { xs: 8, md: 10 },
        pt: { xs: 10, md: 0 },
        maxWidth: 720,
        animation: 'nepheleFadeUp 0.9s ease-out 0.35s both',
      }}
    >
      <Typography
        variant="h1"
        sx={{
          fontSize: { xs: '2.6rem', md: '3.75rem' },
          lineHeight: 1.05,
          mb: 2,
          fontFamily: '"Fraunces", Georgia, serif',
        }}
      >
        Hospitality, held with care.
      </Typography>
      <Typography
        variant="h6"
        sx={{
          fontWeight: 400,
          opacity: 0.92,
          mb: 4,
          maxWidth: 480,
          fontFamily: '"Source Sans 3", sans-serif',
        }}
      >
        One calm system for properties, stays, and guest service across the Aegean and beyond.
      </Typography>
      <HeroActions isLoggedIn={isLoggedIn} navigate={navigate} />
    </Box>
  )
}

export default function LandingPage() {
  const navigate = useNavigate()
  const isLoggedIn = Boolean(localStorage.getItem('access_token'))

  return (
    <Box
      sx={{
        position: 'relative',
        minHeight: '100vh',
        color: 'common.white',
        overflow: 'hidden',
        backgroundImage: `linear-gradient(105deg, rgba(8,72,82,0.82) 0%, rgba(8,72,82,0.35) 48%, rgba(8,72,82,0.2) 100%), url(${HERO_IMAGE})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        animation: 'nepheleHeroIn 1.1s ease-out both',
        '@keyframes nepheleHeroIn': {
          from: { opacity: 0.4, transform: 'scale(1.03)' },
          to: { opacity: 1, transform: 'scale(1)' },
        },
      }}
    >
      <LandingHeader isLoggedIn={isLoggedIn} navigate={navigate} />
      <HeroCopy isLoggedIn={isLoggedIn} navigate={navigate} />
    </Box>
  )
}
