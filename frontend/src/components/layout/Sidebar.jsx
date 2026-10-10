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
  ListSubheader,
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
import { SIDEBAR_ITEMS, groupSidebarItems } from './sidebarConfig'

const DRAWER_WIDTH = 260

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

const ROLE_LABELS = {
  admin: 'Administrator',
  manager: 'Property manager',
  receptionist: 'Reception',
  staff: 'Staff',
  guest: 'Guest',
}

export default function Sidebar({ mobileOpen, onDrawerToggle }) {
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useDispatch()
  const user = useSelector(selectCurrentUser)
  const role = useSelector(selectUserRole)

  const items = SIDEBAR_ITEMS[role] || []
  const groups = groupSidebarItems(items)

  const handleLogout = () => {
    dispatch(clearCredentials())
    navigate('/login', { replace: true })
  }

  const drawerContent = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Toolbar sx={{ px: 2 }}>
        <Typography
          variant="h6"
          sx={{ fontFamily: '"Fraunces", Georgia, serif', color: 'primary.main' }}
        >
          Nephele
        </Typography>
      </Toolbar>
      <Box sx={{ px: 2, pb: 1.5 }}>
        <Typography variant="subtitle2" fontWeight={600} noWrap>
          {user?.username || user?.email || 'User'}
        </Typography>
        <Chip
          label={ROLE_LABELS[role] || role || 'unknown'}
          size="small"
          color="primary"
          variant="outlined"
          sx={{ mt: 0.5 }}
        />
      </Box>
      <Divider />

      <Box sx={{ flex: 1, overflowY: 'auto', py: 1 }}>
        {groups.map((group) => (
          <List
            key={group.name}
            dense
            subheader={
              <ListSubheader
                disableSticky
                sx={{
                  bgcolor: 'transparent',
                  lineHeight: 2.2,
                  fontWeight: 700,
                  color: 'text.secondary',
                  textTransform: 'uppercase',
                  fontSize: '0.68rem',
                  letterSpacing: 0.6,
                }}
              >
                {group.name}
              </ListSubheader>
            }
          >
            {group.items.map((item) => {
              const IconComponent = ICON_MAP[item.icon]
              const isActive =
                location.pathname === item.path ||
                (item.path !== '/' && location.pathname.startsWith(`${item.path}/`))

              return (
                <ListItem key={item.path} disablePadding>
                  <ListItemButton selected={isActive} onClick={() => navigate(item.path)}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {IconComponent ? <IconComponent fontSize="small" /> : null}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{ fontSize: '0.875rem', fontWeight: isActive ? 600 : 500 }}
                    />
                  </ListItemButton>
                </ListItem>
              )
            })}
          </List>
        ))}
      </Box>

      <Divider />
      <Box sx={{ p: 1.5 }}>
        <Button
          fullWidth
          variant="outlined"
          color="inherit"
          startIcon={<Logout />}
          onClick={handleLogout}
          sx={{ justifyContent: 'flex-start' }}
        >
          Sign out
        </Button>
      </Box>
    </Box>
  )

  return (
    <Box component="nav" sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}>
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

export { DRAWER_WIDTH }
