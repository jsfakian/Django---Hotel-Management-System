import React, { useState } from 'react'
import { Box, Toolbar } from '@mui/material'
import TopBar from './TopBar'
import Sidebar from './Sidebar'

const DRAWER_WIDTH = 240

export default function AppLayout({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleDrawerToggle = () => {
    setMobileOpen((prev) => !prev)
  }

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <TopBar onDrawerToggle={handleDrawerToggle} />
      <Sidebar mobileOpen={mobileOpen} onDrawerToggle={handleDrawerToggle} />

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          minHeight: '100vh',
          backgroundColor: 'background.default',
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  )
}
