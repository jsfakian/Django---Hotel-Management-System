import React, { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { Box, CircularProgress } from '@mui/material'
import { selectIsAuthenticated, selectUserRole } from './features/auth/authSlice'
import ProtectedRoute from './components/auth/ProtectedRoute'

// Auth / public
const LoginPage = lazy(() => import('./pages/auth/LoginPage'))
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'))
const ForgotPasswordPage = lazy(() => import('./pages/auth/ForgotPasswordPage'))
const LandingPage = lazy(() => import('./pages/LandingPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))
const PaymentSuccessPage = lazy(() => import('./pages/common/PaymentSuccessPage'))
const PaymentVerifyPage = lazy(() => import('./pages/common/PaymentVerifyPage'))

// Admin — dashboard
const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'))

// Admin — rooms
const RoomsListPage = lazy(() => import('./pages/admin/rooms/RoomsListPage'))
const RoomDetailPage = lazy(() => import('./pages/admin/rooms/RoomDetailPage'))
const RoomFormPage = lazy(() => import('./pages/admin/rooms/RoomFormPage'))

// Admin — properties
const PropertiesListPage = lazy(() => import('./pages/admin/properties/PropertiesListPage'))
const PropertyDetailPage = lazy(() => import('./pages/admin/properties/PropertyDetailPage'))
const PropertyFormPage = lazy(() => import('./pages/admin/properties/PropertyFormPage'))
const TravelAgenciesListPage = lazy(() => import('./pages/admin/travel-agencies/TravelAgenciesListPage'))

// Admin — bookings
const BookingsListPage = lazy(() => import('./pages/admin/bookings/BookingsListPage'))
const BookingDetailPage = lazy(() => import('./pages/admin/bookings/BookingDetailPage'))
const BookingFormPage = lazy(() => import('./pages/admin/bookings/BookingFormPage'))

// Admin — guests
const GuestsListPage = lazy(() => import('./pages/admin/guests/GuestsListPage'))
const GuestDetailPage = lazy(() => import('./pages/admin/guests/GuestDetailPage'))
const GuestFormPage = lazy(() => import('./pages/admin/guests/GuestFormPage'))

// Admin — users
const UsersListPage = lazy(() => import('./pages/admin/users/UsersListPage'))
const UserDetailPage = lazy(() => import('./pages/admin/users/UserDetailPage'))

// Admin — payments
const PaymentsListPage = lazy(() => import('./pages/admin/payments/PaymentsListPage'))
const PaymentDetailPage = lazy(() => import('./pages/admin/payments/PaymentDetailPage'))
const PaymentProcessPage = lazy(() => import('./pages/admin/payments/PaymentProcessPage'))

// Admin — invoices
const InvoicesListPage = lazy(() => import('./pages/admin/invoices/InvoicesListPage'))
const AdminInvoiceDetailPage = lazy(() => import('./pages/admin/invoices/InvoiceDetailPage'))

// Admin — refunds
const RefundsListPage = lazy(() => import('./pages/admin/refunds/RefundsListPage'))
const AdminRefundDetailPage = lazy(() => import('./pages/admin/refunds/RefundDetailPage'))

// Admin — employees
const EmployeesListPage = lazy(() => import('./pages/admin/employees/EmployeesListPage'))
const EmployeeDetailPage = lazy(() => import('./pages/admin/employees/EmployeeDetailPage'))
const EmployeeFormPage = lazy(() => import('./pages/admin/employees/EmployeeFormPage'))

// Admin — events
const EventsListPage = lazy(() => import('./pages/admin/events/EventsListPage'))
const EventDetailPage = lazy(() => import('./pages/admin/events/EventDetailPage'))
const EventFormPage = lazy(() => import('./pages/admin/events/EventFormPage'))

// Admin — contracts
const ContractsListPage = lazy(() => import('./pages/admin/contracts/ContractsListPage'))
const ContractDetailPage = lazy(() => import('./pages/admin/contracts/ContractDetailPage'))
const ContractFormPage = lazy(() => import('./pages/admin/contracts/ContractFormPage'))

// Admin — tasks
const AdminTasksListPage = lazy(() => import('./pages/admin/tasks/TasksListPage'))

// Admin — notifications
const AdminNotificationsListPage = lazy(() => import('./pages/admin/notifications/NotificationsListPage'))
const AdminNotificationPreferencesPage = lazy(() => import('./pages/admin/notifications/NotificationPreferencesPage'))

// Admin — room services
const AdminRoomServicesPage = lazy(() => import('./pages/admin/room-services/RoomServicesPage'))

// Admin — announcements
const AnnouncementsListPage = lazy(() => import('./pages/admin/announcements/AnnouncementsListPage'))

// Admin — storage
const StorageListPage = lazy(() => import('./pages/admin/storage/StorageListPage'))

// Admin — pricing
const PricingAnalysisPage = lazy(() => import('./pages/admin/pricing/PricingAnalysisPage'))

// Admin — channels (OTA)
const ChannelsListPage = lazy(() => import('./pages/admin/channels/ChannelsListPage'))

// Admin — inventory
const InventoryPage = lazy(() => import('./pages/admin/inventory/InventoryPage'))

// Guest — GDPR
const GDPRPage = lazy(() => import('./pages/guest/GDPRPage'))

// Analytics
const AnalyticsHubPage = lazy(() => import('./pages/analytics/AnalyticsHubPage'))
const ExecutiveDashboard = lazy(() => import('./pages/analytics/ExecutiveDashboard'))
const OperationalDashboard = lazy(() => import('./pages/analytics/OperationalDashboard'))
const RevenueAnalyticsPage = lazy(() => import('./pages/analytics/RevenueAnalyticsPage'))
const GuestAnalyticsPage = lazy(() => import('./pages/analytics/GuestAnalyticsPage'))
const ForecastingPage = lazy(() => import('./pages/analytics/ForecastingPage'))
const CustomReportsPage = lazy(() => import('./pages/analytics/CustomReportsPage'))

// Manager
const ManagerDashboard = lazy(() => import('./pages/manager/ManagerDashboard'))

// Receptionist
const ReceptionistDashboard = lazy(() => import('./pages/receptionist/ReceptionistDashboard'))
const ReceptionistBookingsPage = lazy(() => import('./pages/receptionist/BookingsPage'))
const CheckInPage = lazy(() => import('./pages/receptionist/CheckInPage'))
const ReceptionistGuestsPage = lazy(() => import('./pages/receptionist/GuestsPage'))
const ReceptionistPaymentsPage = lazy(() => import('./pages/receptionist/PaymentsPage'))
const ReceptionistRoomsPage = lazy(() => import('./pages/receptionist/RoomsPage'))

// Staff
const StaffDashboard = lazy(() => import('./pages/staff/StaffDashboard'))
const StaffTasksPage = lazy(() => import('./pages/staff/TasksPage'))

// Guest
const GuestDashboard = lazy(() => import('./pages/guest/GuestDashboard'))
const MyBookingsPage = lazy(() => import('./pages/guest/MyBookingsPage'))
const GuestInvoicesPage = lazy(() => import('./pages/guest/InvoicesPage'))
const GuestInvoiceDetailPage = lazy(() => import('./pages/guest/InvoiceDetailPage'))
const GuestRefundRequestPage = lazy(() => import('./pages/guest/RefundRequestPage'))
const GuestEventsPage = lazy(() => import('./pages/guest/EventsPage'))
const GuestNotificationsPage = lazy(() => import('./pages/guest/NotificationsPage'))
const GuestRoomServicesPage = lazy(() => import('./pages/guest/RoomServicesPage'))
const GuestProfilePage = lazy(() => import('./pages/guest/ProfilePage'))

const ROLE_DASHBOARDS = {
  admin: '/admin/dashboard',
  manager: '/manager/dashboard',
  receptionist: '/receptionist/dashboard',
  staff: '/staff/dashboard',
  guest: '/guest/dashboard',
}

const STAFF_ADMIN = ['admin', 'manager', 'receptionist', 'staff']
const ADMIN_MANAGER = ['admin', 'manager']
const RECEPTION_UP = ['admin', 'manager', 'receptionist']
const ALL_ROLES = ['admin', 'manager', 'receptionist', 'staff', 'guest']

function PageLoader() {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
      <CircularProgress />
    </Box>
  )
}

function RootRedirect() {
  const isAuthenticated = useSelector(selectIsAuthenticated)
  const role = useSelector(selectUserRole)
  if (!isAuthenticated) return <Navigate to="/landing" replace />
  return <Navigate to={ROLE_DASHBOARDS[role] || '/login'} replace />
}

function PR({ roles, children }) {
  return <ProtectedRoute allowedRoles={roles}>{children}</ProtectedRoute>
}

export default function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Root */}
        <Route path="/" element={<RootRedirect />} />

        {/* Public */}
        <Route path="/landing" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/payment-success" element={<PaymentSuccessPage />} />
        <Route path="/payments/:id/verify" element={<PR roles={ALL_ROLES}><PaymentVerifyPage /></PR>} />

        {/* ── ADMIN ── */}
        <Route path="/admin/dashboard" element={<PR roles={['admin']}><AdminDashboard /></PR>} />

        {/* Rooms */}
        <Route path="/admin/rooms" element={<PR roles={['admin']}><RoomsListPage /></PR>} />
        <Route path="/admin/rooms/new" element={<PR roles={['admin']}><RoomFormPage /></PR>} />
        <Route path="/admin/rooms/:id" element={<PR roles={['admin']}><RoomDetailPage /></PR>} />
        <Route path="/admin/rooms/:id/edit" element={<PR roles={['admin']}><RoomFormPage /></PR>} />

        {/* Properties */}
        <Route path="/admin/properties" element={<PR roles={['admin']}><PropertiesListPage /></PR>} />
        <Route path="/admin/properties/new" element={<PR roles={['admin']}><PropertyFormPage /></PR>} />
        <Route path="/admin/properties/:id" element={<PR roles={['admin']}><PropertyDetailPage /></PR>} />
        <Route path="/admin/properties/:id/edit" element={<PR roles={['admin']}><PropertyFormPage /></PR>} />
        <Route path="/admin/travel-agencies" element={<PR roles={['admin']}><TravelAgenciesListPage /></PR>} />

        {/* Bookings */}
        <Route path="/admin/bookings" element={<PR roles={['admin']}><BookingsListPage /></PR>} />
        <Route path="/admin/bookings/new" element={<PR roles={['admin']}><BookingFormPage /></PR>} />
        <Route path="/admin/bookings/:id" element={<PR roles={['admin']}><BookingDetailPage /></PR>} />
        <Route path="/admin/bookings/:id/edit" element={<PR roles={['admin']}><BookingFormPage /></PR>} />

        {/* Guests */}
        <Route path="/admin/guests" element={<PR roles={['admin']}><GuestsListPage /></PR>} />
        <Route path="/admin/guests/new" element={<PR roles={['admin']}><GuestFormPage /></PR>} />
        <Route path="/admin/guests/:id" element={<PR roles={['admin']}><GuestDetailPage /></PR>} />
        <Route path="/admin/guests/:id/edit" element={<PR roles={['admin']}><GuestFormPage /></PR>} />

        {/* Users */}
        <Route path="/admin/users" element={<PR roles={['admin']}><UsersListPage /></PR>} />
        <Route path="/admin/users/:id" element={<PR roles={['admin']}><UserDetailPage /></PR>} />

        {/* Payments */}
        <Route path="/admin/payments" element={<PR roles={ADMIN_MANAGER}><PaymentsListPage /></PR>} />
        <Route path="/admin/payments/new" element={<PR roles={ADMIN_MANAGER}><PaymentProcessPage /></PR>} />
        <Route path="/admin/payments/:id" element={<PR roles={ADMIN_MANAGER}><PaymentDetailPage /></PR>} />

        {/* Invoices */}
        <Route path="/admin/invoices" element={<PR roles={ADMIN_MANAGER}><InvoicesListPage /></PR>} />
        <Route path="/admin/invoices/:id" element={<PR roles={ADMIN_MANAGER}><AdminInvoiceDetailPage /></PR>} />

        {/* Refunds */}
        <Route path="/admin/refunds" element={<PR roles={ADMIN_MANAGER}><RefundsListPage /></PR>} />
        <Route path="/admin/refunds/:id" element={<PR roles={ADMIN_MANAGER}><AdminRefundDetailPage /></PR>} />

        {/* Employees */}
        <Route path="/admin/employees" element={<PR roles={['admin']}><EmployeesListPage /></PR>} />
        <Route path="/admin/employees/new" element={<PR roles={['admin']}><EmployeeFormPage /></PR>} />
        <Route path="/admin/employees/:id" element={<PR roles={['admin']}><EmployeeDetailPage /></PR>} />
        <Route path="/admin/employees/:id/edit" element={<PR roles={['admin']}><EmployeeFormPage /></PR>} />

        {/* Events */}
        <Route path="/admin/events" element={<PR roles={ADMIN_MANAGER}><EventsListPage /></PR>} />
        <Route path="/admin/events/new" element={<PR roles={ADMIN_MANAGER}><EventFormPage /></PR>} />
        <Route path="/admin/events/:id" element={<PR roles={ADMIN_MANAGER}><EventDetailPage /></PR>} />
        <Route path="/admin/events/:id/edit" element={<PR roles={ADMIN_MANAGER}><EventFormPage /></PR>} />

        {/* Contracts */}
        <Route path="/admin/contracts" element={<PR roles={ADMIN_MANAGER}><ContractsListPage /></PR>} />
        <Route path="/admin/contracts/new" element={<PR roles={ADMIN_MANAGER}><ContractFormPage /></PR>} />
        <Route path="/admin/contracts/:id" element={<PR roles={ADMIN_MANAGER}><ContractDetailPage /></PR>} />
        <Route path="/admin/contracts/:id/edit" element={<PR roles={ADMIN_MANAGER}><ContractFormPage /></PR>} />

        {/* Tasks */}
        <Route path="/admin/tasks" element={<PR roles={ADMIN_MANAGER}><AdminTasksListPage /></PR>} />

        {/* Notifications */}
        <Route path="/admin/notifications" element={<PR roles={['admin']}><AdminNotificationsListPage /></PR>} />
        <Route path="/admin/notifications/preferences" element={<PR roles={['admin']}><AdminNotificationPreferencesPage /></PR>} />

        {/* Room services */}
        <Route path="/admin/room-services" element={<PR roles={ADMIN_MANAGER}><AdminRoomServicesPage /></PR>} />

        {/* Announcements */}
        <Route path="/admin/announcements" element={<PR roles={ADMIN_MANAGER}><AnnouncementsListPage /></PR>} />

        {/* Storage */}
        <Route path="/admin/storage" element={<PR roles={ADMIN_MANAGER}><StorageListPage /></PR>} />

        {/* Pricing */}
        <Route path="/admin/pricing" element={<PR roles={ADMIN_MANAGER}><PricingAnalysisPage /></PR>} />

        {/* OTA Channels */}
        <Route path="/admin/channels" element={<PR roles={['admin']}><ChannelsListPage /></PR>} />

        {/* Inventory */}
        <Route path="/admin/inventory" element={<PR roles={ADMIN_MANAGER}><InventoryPage /></PR>} />

        {/* ── ANALYTICS ── */}
        <Route path="/analytics" element={<PR roles={ADMIN_MANAGER}><AnalyticsHubPage /></PR>} />
        <Route path="/analytics/executive" element={<PR roles={ADMIN_MANAGER}><ExecutiveDashboard /></PR>} />
        <Route path="/analytics/operational" element={<PR roles={ADMIN_MANAGER}><OperationalDashboard /></PR>} />
        <Route path="/analytics/revenue" element={<PR roles={ADMIN_MANAGER}><RevenueAnalyticsPage /></PR>} />
        <Route path="/analytics/guests" element={<PR roles={ADMIN_MANAGER}><GuestAnalyticsPage /></PR>} />
        <Route path="/analytics/forecasting" element={<PR roles={ADMIN_MANAGER}><ForecastingPage /></PR>} />
        <Route path="/analytics/reports" element={<PR roles={ADMIN_MANAGER}><CustomReportsPage /></PR>} />

        {/* ── MANAGER ── */}
        <Route path="/manager/dashboard" element={<PR roles={['manager']}><ManagerDashboard /></PR>} />
        <Route path="/manager/bookings" element={<PR roles={['manager']}><BookingsListPage /></PR>} />
        <Route path="/manager/rooms" element={<PR roles={['manager']}><RoomsListPage /></PR>} />
        <Route path="/manager/payments" element={<PR roles={['manager']}><PaymentsListPage /></PR>} />
        <Route path="/manager/analytics" element={<PR roles={['manager']}><AnalyticsHubPage /></PR>} />
        <Route path="/manager/events" element={<PR roles={['manager']}><EventsListPage /></PR>} />
        <Route path="/manager/contracts" element={<PR roles={['manager']}><ContractsListPage /></PR>} />
        <Route path="/manager/tasks" element={<PR roles={['manager']}><AdminTasksListPage /></PR>} />
        <Route path="/manager/announcements" element={<PR roles={['manager']}><AnnouncementsListPage /></PR>} />

        {/* ── RECEPTIONIST ── */}
        <Route path="/receptionist/dashboard" element={<PR roles={RECEPTION_UP}><ReceptionistDashboard /></PR>} />
        <Route path="/receptionist/bookings" element={<PR roles={RECEPTION_UP}><ReceptionistBookingsPage /></PR>} />
        <Route path="/receptionist/check-in" element={<PR roles={RECEPTION_UP}><CheckInPage /></PR>} />
        <Route path="/receptionist/guests" element={<PR roles={RECEPTION_UP}><ReceptionistGuestsPage /></PR>} />
        <Route path="/receptionist/payments" element={<PR roles={RECEPTION_UP}><ReceptionistPaymentsPage /></PR>} />
        <Route path="/receptionist/rooms" element={<PR roles={RECEPTION_UP}><ReceptionistRoomsPage /></PR>} />

        {/* ── STAFF ── */}
        <Route path="/staff/dashboard" element={<PR roles={['staff']}><StaffDashboard /></PR>} />
        <Route path="/staff/tasks" element={<PR roles={['staff']}><StaffTasksPage /></PR>} />

        {/* ── GUEST ── */}
        <Route path="/guest/dashboard" element={<PR roles={['guest']}><GuestDashboard /></PR>} />
        <Route path="/guest/bookings" element={<PR roles={['guest']}><MyBookingsPage /></PR>} />
        <Route path="/guest/invoices" element={<PR roles={['guest']}><GuestInvoicesPage /></PR>} />
        <Route path="/guest/invoices/:id" element={<PR roles={['guest']}><GuestInvoiceDetailPage /></PR>} />
        <Route path="/guest/refunds" element={<PR roles={['guest']}><GuestRefundRequestPage /></PR>} />
        <Route path="/guest/events" element={<PR roles={['guest']}><GuestEventsPage /></PR>} />
        <Route path="/guest/notifications" element={<PR roles={['guest']}><GuestNotificationsPage /></PR>} />
        <Route path="/guest/room-services" element={<PR roles={['guest']}><GuestRoomServicesPage /></PR>} />
        <Route path="/guest/profile" element={<PR roles={['guest']}><GuestProfilePage /></PR>} />
        <Route path="/guest/privacy" element={<PR roles={['guest']}><GDPRPage /></PR>} />

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  )
}
