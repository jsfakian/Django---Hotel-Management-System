import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Button, Typography, Grid, Card, CardContent, Container, AppBar, Toolbar } from '@mui/material'
import { Hotel, Analytics, EventNote, Business } from '@mui/icons-material'

const FEATURES = [
  { icon: <Business sx={{ fontSize: 48, color: 'primary.main' }} />, title: 'Multi-Property Management', desc: 'Manage multiple hotels and properties from a single platform with centralized control.' },
  { icon: <Analytics sx={{ fontSize: 48, color: 'secondary.main' }} />, title: 'Real-time Analytics', desc: 'Executive dashboards, revenue analytics, and operational insights at your fingertips.' },
  { icon: <EventNote sx={{ fontSize: 48, color: 'success.main' }} />, title: 'Seamless Bookings', desc: 'Streamlined booking management with check-in/out, dynamic pricing, and guest services.' },
]

export default function LandingPage() {
  const navigate = useNavigate()
  const isLoggedIn = Boolean(localStorage.getItem('access_token'))

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <Hotel sx={{ mr: 1 }} />
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 700 }}>NEPHELE HMS</Typography>
          {isLoggedIn ? (
            <Button color="inherit" onClick={() => navigate('/')}>Go to Dashboard</Button>
          ) : (
            <Button color="inherit" onClick={() => navigate('/login')}>Sign In</Button>
          )}
        </Toolbar>
      </AppBar>

      <Box sx={{ bgcolor: 'primary.dark', color: 'white', py: { xs: 8, md: 12 }, textAlign: 'center' }}>
        <Container maxWidth="md">
          <Hotel sx={{ fontSize: 72, mb: 2, opacity: 0.9 }} />
          <Typography variant="h3" fontWeight={700} gutterBottom>Welcome to NEPHELE HMS</Typography>
          <Typography variant="h6" sx={{ mb: 4, opacity: 0.85 }}>Comprehensive Hotel Management System for modern hospitality businesses</Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            {isLoggedIn ? (
              <Button size="large" variant="contained" color="secondary" onClick={() => navigate('/')}>Go to Dashboard</Button>
            ) : (
              <>
                <Button size="large" variant="contained" color="secondary" onClick={() => navigate('/login')}>Sign In</Button>
                <Button size="large" variant="outlined" sx={{ color: 'white', borderColor: 'white' }} onClick={() => navigate('/register')}>Create Account</Button>
              </>
            )}
          </Box>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ py: 8 }} id="features">
        <Typography variant="h4" fontWeight={700} textAlign="center" gutterBottom>Everything you need to manage your hotel</Typography>
        <Typography variant="body1" color="text.secondary" textAlign="center" sx={{ mb: 6 }}>A complete solution from booking to check-out</Typography>
        <Grid container spacing={4}>
          {FEATURES.map(({ icon, title, desc }) => (
            <Grid item xs={12} sm={4} key={title}>
              <Card sx={{ height: '100%', textAlign: 'center' }}>
                <CardContent sx={{ p: 4 }}>
                  <Box sx={{ mb: 2 }}>{icon}</Box>
                  <Typography variant="h6" fontWeight={700} gutterBottom>{title}</Typography>
                  <Typography variant="body2" color="text.secondary">{desc}</Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      <Box sx={{ bgcolor: 'grey.100', py: 3, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">© {new Date().getFullYear()} NEPHELE HMS. All rights reserved.</Typography>
      </Box>
    </Box>
  )
}
