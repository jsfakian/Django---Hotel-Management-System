import React, { useState } from 'react'
import { useNavigate, useLocation, Link as RouterLink } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import {
  AppBar,
  Box,
  Button,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import {
  Menu as MenuIcon,
  EventNote,
  Receipt,
  RoomService,
  Event,
  AccountCircle,
  Shield,
  Notifications,
  MoneyOff,
  Logout,
  HomeOutlined,
} from '@mui/icons-material'
import { clearCredentials, selectCurrentUser } from '../../features/auth/authSlice'
import { useLogoutMutation } from '../../features/auth/authApi'

const NAV = [
  { label: 'Home', path: '/guest/dashboard', icon: HomeOutlined },
  { label: 'Stays', path: '/guest/bookings', icon: EventNote },
  { label: 'Invoices', path: '/guest/invoices', icon: Receipt },
  { label: 'Services', path: '/guest/room-services', icon: RoomService },
  { label: 'Events', path: '/guest/events', icon: Event },
  { label: 'Profile', path: '/guest/profile', icon: AccountCircle },
  { label: 'Privacy', path: '/guest/privacy', icon: Shield },
]

const SECONDARY = [
  { label: 'Notifications', path: '/guest/notifications', icon: Notifications },
  { label: 'Refunds', path: '/guest/refunds', icon: MoneyOff },
]

function GuestDrawerNav({ pathname, onNavigate, onLogout }) {
  return (
    <Box sx={{ width: 280, py: 2 }} role="navigation" aria-label="Guest">
      <Typography
        variant="h5"
        sx={{ px: 3, mb: 2, fontFamily: '"Fraunces", Georgia, serif', color: 'primary.main' }}
      >
        Nephele
      </Typography>
      <List>
        {[...NAV, ...SECONDARY].map(({ label, path, icon: Icon }) => (
          <ListItemButton key={path} selected={pathname.startsWith(path)} onClick={() => onNavigate(path)}>
            <ListItemIcon sx={{ minWidth: 40 }}>
              <Icon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary={label} />
          </ListItemButton>
        ))}
        <ListItemButton onClick={onLogout}>
          <ListItemIcon sx={{ minWidth: 40 }}>
            <Logout fontSize="small" />
          </ListItemIcon>
          <ListItemText primary="Sign out" />
        </ListItemButton>
      </List>
    </Box>
  )
}

function DesktopNav({ pathname, onNavigate }) {
  return (
    <Box sx={{ display: 'flex', gap: 0.5, flexGrow: 1 }}>
      {NAV.map(({ label, path }) => {
        const active = pathname.startsWith(path)
        return (
          <Button
            key={path}
            color={active ? 'primary' : 'inherit'}
            onClick={() => onNavigate(path)}
            sx={{
              fontWeight: active ? 700 : 500,
              bgcolor: active ? 'rgba(11,95,107,0.08)' : 'transparent',
            }}
          >
            {label}
          </Button>
        )
      })}
    </Box>
  )
}

function GuestAppBar({ isMobile, pathname, user, onOpenMenu, onNavigate, onLogout }) {
  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        bgcolor: 'background.paper',
        color: 'text.primary',
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Toolbar sx={{ gap: 1, px: { xs: 2, md: 4 } }}>
        {isMobile && (
          <IconButton edge="start" onClick={onOpenMenu} aria-label="Open menu">
            <MenuIcon />
          </IconButton>
        )}
        <Typography
          component={RouterLink}
          to="/guest/dashboard"
          variant="h5"
          sx={{
            textDecoration: 'none',
            color: 'primary.main',
            fontFamily: '"Fraunces", Georgia, serif',
            mr: 3,
          }}
        >
          Nephele
        </Typography>

        {!isMobile && <DesktopNav pathname={pathname} onNavigate={onNavigate} />}

        <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ display: { xs: 'none', sm: 'block' } }}>
            {user?.first_name || user?.username || 'Guest'}
          </Typography>
          <Button color="inherit" size="small" onClick={onLogout} startIcon={<Logout />}>
            Sign out
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default function GuestLayout({ children }) {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useDispatch()
  const user = useSelector(selectCurrentUser)
  const [logout] = useLogoutMutation()

  const handleLogout = async () => {
    const refresh = localStorage.getItem('refresh_token')
    try {
      if (refresh) await logout({ refresh }).unwrap()
    } catch {
      /* clear locally anyway */
    }
    dispatch(clearCredentials())
    navigate('/login', { replace: true })
  }

  const handleDrawerNavigate = (path) => {
    navigate(path)
    setOpen(false)
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <GuestAppBar
        isMobile={isMobile}
        pathname={location.pathname}
        user={user}
        onOpenMenu={() => setOpen(true)}
        onNavigate={navigate}
        onLogout={handleLogout}
      />

      <Drawer open={open} onClose={() => setOpen(false)}>
        <GuestDrawerNav pathname={location.pathname} onNavigate={handleDrawerNavigate} onLogout={handleLogout} />
      </Drawer>

      <Box
        component="main"
        sx={{
          maxWidth: 1100,
          mx: 'auto',
          px: { xs: 2, md: 4 },
          py: { xs: 3, md: 5 },
        }}
      >
        {children}
      </Box>
    </Box>
  )
}
