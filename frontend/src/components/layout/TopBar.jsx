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
} from '@mui/material'
import {
  Menu as MenuIcon,
  Notifications,
  AccountCircle,
  Logout,
} from '@mui/icons-material'
import { clearCredentials, selectCurrentUser } from '../../features/auth/authSlice'

const DRAWER_WIDTH = 240

export default function TopBar({ onDrawerToggle }) {
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const user = useSelector(selectCurrentUser)

  const [anchorEl, setAnchorEl] = useState(null)

  const handleMenuOpen = (event) => setAnchorEl(event.currentTarget)
  const handleMenuClose = () => setAnchorEl(null)

  const handleProfile = () => {
    handleMenuClose()
    navigate('/guest/profile')
  }

  const handleLogout = () => {
    handleMenuClose()
    dispatch(clearCredentials())
    navigate('/login', { replace: true })
  }

  const userInitial = user?.username
    ? user.username[0].toUpperCase()
    : user?.email
    ? user.email[0].toUpperCase()
    : 'U'

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

        <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 700 }}>
          NEPHELE HMS
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <IconButton color="inherit">
            <Badge badgeContent={0} color="error">
              <Notifications />
            </Badge>
          </IconButton>

          <IconButton onClick={handleMenuOpen} size="small" sx={{ ml: 1 }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main', fontSize: '0.875rem' }}>
              {userInitial}
            </Avatar>
          </IconButton>
        </Box>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
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
          <MenuItem onClick={handleProfile}>
            <ListItemIcon>
              <AccountCircle fontSize="small" />
            </ListItemIcon>
            <ListItemText>Profile</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleLogout}>
            <ListItemIcon>
              <Logout fontSize="small" />
            </ListItemIcon>
            <ListItemText>Logout</ListItemText>
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  )
}
