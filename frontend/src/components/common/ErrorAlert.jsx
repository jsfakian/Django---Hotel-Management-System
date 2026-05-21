import React from 'react'
import { Alert, AlertTitle } from '@mui/material'

const extractMessage = (error) => {
  if (!error) return 'An unexpected error occurred.'
  if (typeof error === 'string') return error

  const data = error.data
  if (!data) return `Error ${error.status || ''}: An unexpected error occurred.`

  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  if (data.non_field_errors) return data.non_field_errors.join(' ')

  // Collect field-level errors
  const fieldErrors = Object.entries(data)
    .filter(([, val]) => val)
    .map(([field, messages]) => {
      const msg = Array.isArray(messages) ? messages.join(' ') : String(messages)
      return `${field}: ${msg}`
    })
    .join('; ')

  return fieldErrors || `Error ${error.status || ''}: An unexpected error occurred.`
}

export default function ErrorAlert({ error, title }) {
  const message = extractMessage(error)

  return (
    <Alert severity="error" sx={{ mt: 2 }}>
      {title && <AlertTitle>{title}</AlertTitle>}
      {message}
    </Alert>
  )
}
