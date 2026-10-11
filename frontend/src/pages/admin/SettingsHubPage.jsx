import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import {
  Box, Typography, Grid, Paper, List, ListItemButton, ListItemIcon, ListItemText,
} from '@mui/material'
import {
  Business, DirectionsBus, BadgeOutlined, MeetingRoom, Category, LocalOffer,
  CalendarMonth, GridView, Receipt, MoneyOff, Description, TrendingUp,
  Assignment, RoomService, Event, Campaign, Inventory, People, Notifications,
} from '@mui/icons-material'
import AppLayout from '../../components/layout/AppLayout'
import PageHeader from '../../components/common/PageHeader'
import { SETTINGS_SECTIONS } from '../../components/layout/sidebarConfig'
import { selectUserRole } from '../../features/auth/authSlice'

const ICON_MAP = {
  Business,
  DirectionsBus,
  BadgeOutlined,
  MeetingRoom,
  Category,
  LocalOffer,
  CalendarMonth,
  GridView,
  Receipt,
  MoneyOff,
  Description,
  TrendingUp,
  Assignment,
  RoomService,
  Event,
  Campaign,
  Inventory,
  People,
  Notifications,
}

function SettingsSection({ section, onNavigate }) {
  return (
    <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
      <Typography variant="subtitle1" fontWeight={700} sx={{ mb: 0.5 }}>
        {section.name}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
        {section.description}
      </Typography>
      <List dense disablePadding>
        {section.items.map((item) => {
          const Icon = ICON_MAP[item.icon]
          return (
            <ListItemButton
              key={item.path}
              onClick={() => onNavigate(item.path)}
              sx={{ borderRadius: 1, px: 1 }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>
                {Icon ? <Icon fontSize="small" color="primary" /> : null}
              </ListItemIcon>
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{ fontSize: '0.9rem', fontWeight: 500 }}
              />
            </ListItemButton>
          )
        })}
      </List>
    </Paper>
  )
}

export default function SettingsHubPage() {
  const navigate = useNavigate()
  const role = useSelector(selectUserRole)
  const sections = SETTINGS_SECTIONS[role] || SETTINGS_SECTIONS.admin

  return (
    <AppLayout>
      <PageHeader
        title="Settings"
        subtitle="Property setup, billing extras, and system tools — kept out of the daily menu."
      />
      <Box sx={{ mt: 1 }}>
        <Grid container spacing={2}>
          {sections.map((section) => (
            <Grid item xs={12} sm={6} md={4} key={section.name}>
              <SettingsSection section={section} onNavigate={navigate} />
            </Grid>
          ))}
        </Grid>
      </Box>
    </AppLayout>
  )
}
