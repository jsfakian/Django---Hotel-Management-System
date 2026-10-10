import React from 'react'
import { Box, Button, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { BookingLangProvider } from './bookingI18n'
import { useBookingT } from './bookingLang'

const HERO_IMAGE =
  'https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=2000&q=80'

function ShellInner({ children, subtitle, subtitleKey }) {
  const navigate = useNavigate()
  const { t, toggleLang } = useBookingT()
  const resolvedSubtitle = subtitleKey ? t(subtitleKey) : subtitle

  return (
    <Box
      sx={{
        minHeight: '100vh',
        color: 'text.primary',
        background: `linear-gradient(180deg, rgba(8,72,82,0.92) 0%, rgba(8,72,82,0.75) 280px, #F7F4EF 280px), url(${HERO_IMAGE})`,
        backgroundSize: 'cover, cover',
        backgroundPosition: 'center top',
        backgroundRepeat: 'no-repeat',
      }}
    >
      <Box
        component="header"
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: { xs: 3, md: 6 },
          py: 3,
          color: 'common.white',
          gap: 1,
          flexWrap: 'wrap',
        }}
      >
        <Typography
          variant="h4"
          sx={{ fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600, cursor: 'pointer' }}
          onClick={() => navigate('/landing')}
        >
          Nephele
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            color="inherit"
            variant="outlined"
            size="small"
            onClick={toggleLang}
            sx={{ borderColor: 'rgba(255,255,255,0.55)', color: 'common.white', minWidth: 48 }}
          >
            {t('langToggle')}
          </Button>
          <Button
            color="inherit"
            variant="outlined"
            onClick={() => navigate('/book')}
            sx={{ borderColor: 'rgba(255,255,255,0.55)', color: 'common.white' }}
          >
            {t('bookCta')}
          </Button>
        </Box>
      </Box>

      <Box sx={{ px: { xs: 3, md: 6 }, pb: 2, color: 'common.white', maxWidth: 720 }}>
        <Typography variant="h3" sx={{ fontFamily: '"Fraunces", Georgia, serif', mb: 1 }}>
          {t('bookStay')}
        </Typography>
        {resolvedSubtitle && (
          <Typography variant="body1" sx={{ opacity: 0.9, mb: 2, fontFamily: '"Source Sans 3", sans-serif' }}>
            {resolvedSubtitle}
          </Typography>
        )}
      </Box>

      <Box
        sx={{
          mx: { xs: 2, md: 6 },
          mb: 6,
          p: { xs: 2.5, md: 4 },
          borderRadius: 2,
          bgcolor: 'background.paper',
          boxShadow: '0 12px 40px rgba(8,72,82,0.12)',
          maxWidth: 960,
        }}
      >
        {children}
      </Box>
    </Box>
  )
}

export default function BookingShell({ children, subtitle, subtitleKey }) {
  return (
    <BookingLangProvider>
      <ShellInner subtitle={subtitle} subtitleKey={subtitleKey}>{children}</ShellInner>
    </BookingLangProvider>
  )
}
