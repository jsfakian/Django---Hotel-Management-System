import React from 'react'
import { Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { selectIsAuthenticated, selectUserRole } from '../../features/auth/authSlice'

const ROLE_DASHBOARDS = {
  admin: '/admin/dashboard',
  manager: '/manager/dashboard',
  receptionist: '/receptionist/dashboard',
  staff: '/staff/dashboard',
  guest: '/guest/dashboard',
}

export default function ProtectedRoute({ children, allowedRoles }) {
  const isAuthenticated = useSelector(selectIsAuthenticated)
  const role = useSelector(selectUserRole)

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && role && !allowedRoles.includes(role)) {
    const dashboard = ROLE_DASHBOARDS[role] || '/login'
    return <Navigate to={dashboard} replace />
  }

  return children
}
