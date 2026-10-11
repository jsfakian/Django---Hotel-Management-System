import React from 'react'
import AppLayout from '../layout/AppLayout'

/** Wrap page body in AppLayout unless embedded inside a hub (tabs). */
export default function PageShell({ embedded = false, children }) {
  if (embedded) return children
  return <AppLayout>{children}</AppLayout>
}
