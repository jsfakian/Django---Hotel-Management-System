import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Badge,
  Avatar,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Chip,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Notifications,
  AccountCircle,
  Logout,
  Settings,
} from '@mui/icons-material'
import { clearCredentials, selectCurrentUser, selectUserRole } from '../../features/auth/authSlice'
import { useLogoutMutation } from '../../features/auth/authApi'
import { DRAWER_WIDTH } from './Sidebar'

const ROLE_LABELS = {
  admin: 'Administrator',
  manager: 'Manager',
  receptionist: 'Reception',
  staff: 'Staff',
  guest: 'Guest',
}

function UserAccountMenu({ user, role, anchorEl, onClose, onProfile, onSettings, onLogout }) {
  return (
    <Menu
      anchorEl={anchorEl}
      open={Boolean(anchorEl)}
      onClose={onClose}
      transformOrigin={{ horizontal: 'right', vertical: 'top' }}
      anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      PaperProps={{ elevation: 2, sx: { minWidth: 180 } }}
    >
      <Box sx={{ px: 2, py: 1 }}>
        <Typography variant="subtitle2" fontWeight={600}>
          {user?.username || 'User'}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {user?.email}
        </Typography>
      </Box>
      <Divider />
      <MenuItem onClick={onProfile}>
        <ListItemIcon><AccountCircle fontSize="small" /></ListItemIcon>
        <ListItemText>Profile</ListItemText>
      </MenuItem>
      {(role === 'admin' || role === 'manager') && (
        <MenuItem onClick={onSettings}>
          <ListItemIcon><Settings fontSize="small" /></ListItemIcon>
          <ListItemText>Settings</ListItemText>
        </MenuItem>
      )}
      <MenuItem onClick={onLogout}>
        <ListItemIcon><Logout fontSize="small" /></ListItemIcon>
        <ListItemText>Logout</ListItemText>
      </MenuItem>
    </Menu>
  )
}

export default function TopBar({ onDrawerToggle }) {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const user = useSelector(selectCurrentUser)
  const role = useSelector(selectUserRole)
  const [logout] = useLogoutMutation()
  const [anchorEl, setAnchorEl] = useState(null)

  const closeMenu = () => setAnchorEl(null)

  const handleLogout = async () => {
    closeMenu()
    const refresh = localStorage.getItem('refresh_token')
    try {
      if (refresh) await logout({ refresh }).unwrap()
    } catch {
      // Still clear local session if blacklist fails
    }
    dispatch(clearCredentials())
    navigate('/login', { replace: true })
  }

  const userInitial = (user?.username || user?.email || 'U')[0].toUpperCase()

  return (
    <AppBar
      position="fixed"
      elevation={1}
      sx={{
        width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
        ml: { md: `${DRAWER_WIDTH}px` },
        backgroundColor: 'background.paper',
        color: 'text.primary',
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Toolbar>
        <IconButton
          color="inherit"
          edge="start"
          onClick={onDrawerToggle}
          sx={{ mr: 2, display: { md: 'none' } }}
        >
          <MenuIcon />
        </IconButton>

        <Typography
          variant="h6"
          component="div"
          sx={{ fontFamily: '"Fraunces", Georgia, serif', fontWeight: 600, mr: 2 }}
        >
          Nephele
        </Typography>
        <Chip
          size="small"
          label={ROLE_LABELS[role] || role || 'Workspace'}
          color="primary"
          variant="outlined"
          sx={{ mr: 'auto', display: { xs: 'none', sm: 'inline-flex' } }}
        />

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <IconButton color="inherit" aria-label="Notifications">
            <Badge badgeContent={0} color="error">
              <Notifications />
            </Badge>
          </IconButton>
          <IconButton onClick={(e) => setAnchorEl(e.currentTarget)} size="small" sx={{ ml: 1 }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main', fontSize: '0.875rem' }}>
              {userInitial}
            </Avatar>
          </IconButton>
        </Box>

        <UserAccountMenu
          user={user}
          role={role}
          anchorEl={anchorEl}
          onClose={closeMenu}
          onProfile={() => {
            closeMenu()
            navigate(role === 'guest' ? '/guest/profile' : `/${role}/dashboard`)
          }}
          onSettings={() => {
            closeMenu()
            navigate(role === 'manager' ? '/manager/settings' : '/admin/settings')
          }}
          onLogout={handleLogout}
        />
      </Toolbar>
    </AppBar>
  )
}
