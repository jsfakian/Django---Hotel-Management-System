import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Box,
  Chip,
  Typography,
  Divider,
  Button,
} from '@mui/material'
import {
  Dashboard,
  People,
  Business,
  MeetingRoom,
  EventNote,
  Payment,
  BarChart,
  Description,
  Assessment,
  HotelOutlined,
  Assignment,
  Build,
  Receipt,
  AccountCircle,
  Logout,
  BadgeOutlined,
  DirectionsBus,
  PersonOutline,
  MoneyOff,
  Event,
  RoomService,
  Campaign,
  Inventory,
  TrendingUp,
  Notifications,
  CloudSync,
  GridView,
  Shield,
} from '@mui/icons-material'
import { clearCredentials, selectCurrentUser, selectUserRole } from '../../features/auth/authSlice'
import { SIDEBAR_ITEMS } from './sidebarConfig'

const DRAWER_WIDTH = 240

const ICON_MAP = {
  Dashboard,
  People,
  Business,
  MeetingRoom,
  EventNote,
  Payment,
  BarChart,
  Description,
  Assessment,
  HotelOutlined,
  Assignment,
  Build,
  Receipt,
  AccountCircle,
  BadgeOutlined,
  DirectionsBus,
  PersonOutline,
  MoneyOff,
  Event,
  RoomService,
  Campaign,
  Inventory,
  TrendingUp,
  Notifications,
  CloudSync,
  GridView,
  Shield,
}

const ROLE_COLORS = {
  admin: 'error',
  manager: 'warning',
  receptionist: 'info',
  staff: 'success',
  guest: 'secondary',
}

export default function Sidebar({ mobileOpen, onDrawerToggle }) {
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useDispatch()
  const user = useSelector(selectCurrentUser)
  const role = useSelector(selectUserRole)

  const items = SIDEBAR_ITEMS[role] || []

  const handleLogout = () => {
    dispatch(clearCredentials())
    navigate('/login', { replace: true })
  }

  const drawerContent = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Toolbar />
      {/* User info */}
      <Box sx={{ px: 2, py: 1.5 }}>
        <Typography variant="subtitle2" fontWeight={600} noWrap>
          {user?.username || user?.email || 'User'}
        </Typography>
        <Chip
          label={role || 'unknown'}
          size="small"
          color={ROLE_COLORS[role] || 'default'}
          sx={{ mt: 0.5, textTransform: 'capitalize' }}
        />
      </Box>
      <Divider />

      {/* Navigation items */}
      <List sx={{ flex: 1, py: 1 }}>
        {items.map((item) => {
          const IconComponent = ICON_MAP[item.icon]
          const isActive = location.pathname === item.path

          return (
            <ListItem key={item.path} disablePadding>
              <ListItemButton
                selected={isActive}
                onClick={() => navigate(item.path)}
                sx={{
                  mx: 1,
                  borderRadius: 1,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.main',
                    color: 'primary.contrastText',
                    '& .MuiListItemIcon-root': {
                      color: 'primary.contrastText',
                    },
                    '&:hover': {
                      backgroundColor: 'primary.dark',
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  {IconComponent ? <IconComponent fontSize="small" /> : null}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{ fontSize: '0.875rem' }}
                />
              </ListItemButton>
            </ListItem>
          )
        })}
      </List>

      <Divider />
      {/* Logout */}
      <Box sx={{ p: 1.5 }}>
        <Button
          fullWidth
          variant="outlined"
          color="inherit"
          startIcon={<Logout />}
          onClick={handleLogout}
          sx={{ justifyContent: 'flex-start' }}
        >
          Logout
        </Button>
      </Box>
    </Box>
  )

  return (
    <Box
      component="nav"
      sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
    >
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onDrawerToggle}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: DRAWER_WIDTH },
        }}
        open
      >
        {drawerContent}
      </Drawer>
    </Box>
  )
}
