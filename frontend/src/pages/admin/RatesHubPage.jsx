import React, { Suspense, lazy } from 'react'
import { Navigate, useSearchParams } from 'react-router-dom'
import { Box, Tabs, Tab, CircularProgress } from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import PageHeader from '../../components/common/PageHeader'

const RoomTypesPage = lazy(() => import('./catalog/RoomTypesPage'))
const RatePlansPage = lazy(() => import('./catalog/RatePlansPage'))
const AvailabilityCalendarPage = lazy(() => import('./catalog/AvailabilityCalendarPage'))
const InventoryPage = lazy(() => import('./inventory/InventoryPage'))

const TABS = [
  { key: 'room-types', label: 'Room types' },
  { key: 'rate-plans', label: 'Rate plans' },
  { key: 'availability', label: 'Availability' },
  { key: 'inventory', label: 'Inventory' },
]

const LEGACY_TAB = {
  'room-types': 'room-types',
  'rate-plans': 'rate-plans',
  'availability-calendar': 'availability',
  inventory: 'inventory',
}

function TabPanel({ tab }) {
  switch (tab) {
    case 'rate-plans':
      return <RatePlansPage embedded />
    case 'availability':
      return <AvailabilityCalendarPage embedded />
    case 'inventory':
      return <InventoryPage embedded />
    default:
      return <RoomTypesPage embedded />
  }
}

export default function RatesHubPage() {
  const [params, setParams] = useSearchParams()
  const raw = params.get('tab') || 'room-types'
  const tab = LEGACY_TAB[raw] || (TABS.some((t) => t.key === raw) ? raw : 'room-types')

  if (raw !== tab) {
    return <Navigate to={`/admin/rates?tab=${tab}`} replace />
  }

  return (
    <AppLayout>
      <PageHeader
        title="Rates & availability"
        subtitle="Room types, plans, allotment, and inventory."
      />
      <Tabs
        value={tab}
        onChange={(_, next) => setParams({ tab: next }, { replace: true })}
        sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
        variant="scrollable"
        allowScrollButtonsMobile
      >
        {TABS.map((t) => (
          <Tab key={t.key} value={t.key} label={t.label} />
        ))}
      </Tabs>
      <Box>
        <Suspense fallback={<Box sx={{ py: 6, textAlign: 'center' }}><CircularProgress /></Box>}>
          <TabPanel tab={tab} />
        </Suspense>
      </Box>
    </AppLayout>
  )
}
