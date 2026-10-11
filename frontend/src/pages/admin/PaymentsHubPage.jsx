import React, { Suspense, lazy } from 'react'
import { Navigate, useSearchParams } from 'react-router-dom'
import { Box, Tabs, Tab, CircularProgress } from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import PageHeader from '../../components/common/PageHeader'

const PaymentsListPage = lazy(() => import('./payments/PaymentsListPage'))
const InvoicesListPage = lazy(() => import('./invoices/InvoicesListPage'))
const RefundsListPage = lazy(() => import('./refunds/RefundsListPage'))

const TABS = [
  { key: 'payments', label: 'Payments' },
  { key: 'invoices', label: 'Invoices' },
  { key: 'refunds', label: 'Refunds' },
]

function TabPanel({ tab }) {
  if (tab === 'invoices') return <InvoicesListPage embedded />
  if (tab === 'refunds') return <RefundsListPage embedded />
  return <PaymentsListPage embedded />
}

export default function PaymentsHubPage() {
  const [params, setParams] = useSearchParams()
  const raw = params.get('tab') || 'payments'
  const tab = TABS.some((t) => t.key === raw) ? raw : 'payments'

  if (raw !== tab) {
    return <Navigate to={`/admin/payments?tab=${tab}`} replace />
  }

  return (
    <AppLayout>
      <PageHeader
        title="Payments"
        subtitle="Payments, invoices, and refunds in one place."
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
