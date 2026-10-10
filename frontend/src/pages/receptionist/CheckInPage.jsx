import React, { useEffect, useState } from 'react'
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  Divider,
  CircularProgress,
  Alert,
  MenuItem,
} from '@mui/material'
import { Search, Login as CheckInIcon, Logout as CheckOutIcon } from '@mui/icons-material'
import {
  useGetBookingQuery,
  useCheckInMutation,
  useCheckOutMutation,
  useUpdateBookingMutation,
} from '../../features/bookings/bookingsApi'
import ErrorAlert from '../../components/common/ErrorAlert'
import PageHeader from '../../components/common/PageHeader'
import EmptyState from '../../components/common/EmptyState'
import AppLayout from '../../components/layout/AppLayout'
import PoliceSheetExport from './PoliceSheetExport'

const STATUS_COLORS = {
  confirmed: 'success',
  pending: 'warning',
  checked_in: 'info',
  checked_out: 'default',
  cancelled: 'error',
}

const STAY_PURPOSES = [
  { value: '', label: '—' },
  { value: 'tourism', label: 'Tourism' },
  { value: 'business', label: 'Business' },
  { value: 'other', label: 'Other' },
]

const formatDate = (dateStr) => {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

const DASH = '—'

function Field({ label, children }) {
  return (
    <Grid item xs={12} sm={6}>
      <Typography variant="body2" color="text.secondary">{label}</Typography>
      <Typography variant="body1" fontWeight={500}>{children}</Typography>
    </Grid>
  )
}

const guestLabel = (b) => b.guest_name || b.guest?.full_name || b.guest?.username || DASH
const roomLabel = (b) => b.room_number || b.room?.number || b.room || DASH

function complianceFromBooking(booking) {
  return {
    guest_document_type: booking.guest_document_type || '',
    guest_document_number: booking.guest_document_number || '',
    guest_nationality: booking.guest_nationality || '',
    guest_birth_date: booking.guest_birth_date || '',
    shima_stay_purpose: booking.shima_stay_purpose || '',
  }
}

function ComplianceForm({ form, setForm, onSave, saving }) {
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))
  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>Guest compliance (ΣΑΕ / ΣΗΜΑ)</Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <TextField fullWidth size="small" label="Document type" value={form.guest_document_type} onChange={set('guest_document_type')} />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField fullWidth size="small" label="Document number" value={form.guest_document_number} onChange={set('guest_document_number')} />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField fullWidth size="small" label="Nationality" value={form.guest_nationality} onChange={set('guest_nationality')} />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            size="small"
            type="date"
            label="Birth date"
            InputLabelProps={{ shrink: true }}
            value={form.guest_birth_date || ''}
            onChange={set('guest_birth_date')}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <TextField
            select
            fullWidth
            size="small"
            label="Stay purpose (ΣΗΜΑ)"
            value={form.shima_stay_purpose}
            onChange={set('shima_stay_purpose')}
          >
            {STAY_PURPOSES.map((p) => (
              <MenuItem key={p.value || 'empty'} value={p.value}>{p.label}</MenuItem>
            ))}
          </TextField>
        </Grid>
        <Grid item xs={12}>
          <Button variant="outlined" size="small" onClick={onSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save compliance'}
          </Button>
        </Grid>
      </Grid>
    </Box>
  )
}

function BookingDetails({ booking }) {
  return (
    <Grid container spacing={2}>
      <Field label="Guest">{guestLabel(booking)}</Field>
      <Field label="Room">{roomLabel(booking)}</Field>
      <Field label="Check-in Date">{formatDate(booking.check_in_date)}</Field>
      <Field label="Check-out Date">{formatDate(booking.check_out_date)}</Field>
      {booking.total_price != null && (
        <Field label="Total Price">€{Number(booking.total_price).toLocaleString()}</Field>
      )}
    </Grid>
  )
}

function ActionButton({ color, icon, busy, onClick, label }) {
  return (
    <Button variant="contained" color={color} startIcon={icon} disabled={busy} onClick={onClick}>
      {busy ? <CircularProgress size={20} color="inherit" /> : label}
    </Button>
  )
}

function BookingActions({ booking, checkingIn, checkingOut, onCheckIn, onCheckOut }) {
  const { status } = booking
  return (
    <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
      {status === 'confirmed' && (
        <ActionButton color="success" icon={<CheckInIcon />} busy={checkingIn} onClick={onCheckIn} label="Confirm Check-In" />
      )}
      {status === 'checked_in' && (
        <ActionButton color="warning" icon={<CheckOutIcon />} busy={checkingOut} onClick={onCheckOut} label="Confirm Check-Out" />
      )}
      {status !== 'confirmed' && status !== 'checked_in' && (
        <Typography variant="body2" color="text.secondary">
          No actions available for status: {status}
        </Typography>
      )}
    </Box>
  )
}

function BookingCard({ booking, compliance, setCompliance, onSaveCompliance, savingCompliance, ...actions }) {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Booking #{booking.id}</Typography>
          <Chip
            label={booking.status?.replace('_', ' ')}
            color={STATUS_COLORS[booking.status] || 'default'}
            sx={{ textTransform: 'capitalize' }}
          />
        </Box>
        <Divider sx={{ mb: 2 }} />
        <BookingDetails booking={booking} />
        <ComplianceForm
          form={compliance}
          setForm={setCompliance}
          onSave={onSaveCompliance}
          saving={savingCompliance}
        />
        <BookingActions booking={booking} {...actions} />
      </CardContent>
    </Card>
  )
}

function LookupForm({ value, onChange, onSubmit }) {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box component="form" onSubmit={onSubmit} sx={{ display: 'flex', gap: 2 }}>
          <TextField
            label="Booking ID"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            size="small"
            type="number"
            sx={{ width: 200 }}
            required
          />
          <Button type="submit" variant="contained" startIcon={<Search />}>
            Look Up
          </Button>
        </Box>
      </CardContent>
    </Card>
  )
}

export default function CheckInPage() {
  const [bookingId, setBookingId] = useState('')
  const [searchId, setSearchId] = useState(null)
  const [successMsg, setSuccessMsg] = useState('')
  const [compliance, setCompliance] = useState(complianceFromBooking({}))

  const {
    data: booking,
    isLoading: loadingBooking,
    error: bookingError,
  } = useGetBookingQuery(searchId, { skip: !searchId })

  const [checkIn, { isLoading: checkingIn, error: checkInError }] = useCheckInMutation()
  const [checkOut, { isLoading: checkingOut, error: checkOutError }] = useCheckOutMutation()
  const [updateBooking, { isLoading: savingCompliance, error: complianceError }] = useUpdateBookingMutation()

  useEffect(() => {
    if (booking) setCompliance(complianceFromBooking(booking))
  }, [booking])

  const handleSearch = (e) => {
    e.preventDefault()
    setSuccessMsg('')
    const id = parseInt(bookingId, 10)
    if (id) setSearchId(id)
  }

  const handleCheckIn = async () => {
    try {
      await checkIn(booking.id).unwrap()
      setSuccessMsg(`Booking #${booking.id} checked in successfully.`)
    } catch {
      // handled by RTK error state
    }
  }

  const handleCheckOut = async () => {
    try {
      await checkOut(booking.id).unwrap()
      setSuccessMsg(`Booking #${booking.id} checked out successfully.`)
    } catch {
      // handled by RTK error state
    }
  }

  const handleSaveCompliance = async () => {
    setSuccessMsg('')
    const result = await updateBooking({
      id: booking.id,
      guest_document_type: compliance.guest_document_type,
      guest_document_number: compliance.guest_document_number,
      guest_nationality: compliance.guest_nationality,
      guest_birth_date: compliance.guest_birth_date || null,
      shima_stay_purpose: compliance.shima_stay_purpose,
    })
    if (!result.error) setSuccessMsg('Compliance fields saved.')
  }

  return (
    <AppLayout>
      <PageHeader
        title="Check-In / Check-Out"
        subtitle="Look up a booking by ID to arrive or depart a guest"
      />

      <PoliceSheetExport />

      <LookupForm value={bookingId} onChange={setBookingId} onSubmit={handleSearch} />

      {!searchId && !loadingBooking && (
        <EmptyState
          title="Ready for the next arrival"
          description="Enter a booking ID above to check a guest in or out."
          icon={<Search fontSize="large" />}
        />
      )}

      {loadingBooking && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {bookingError && <ErrorAlert error={bookingError} title="Booking not found" />}
      {checkInError && <ErrorAlert error={checkInError} title="Check-in failed" />}
      {checkOutError && <ErrorAlert error={checkOutError} title="Check-out failed" />}
      {complianceError && <ErrorAlert error={complianceError} title="Compliance save failed" />}
      {successMsg && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {successMsg}
        </Alert>
      )}
      {booking && (
        <BookingCard
          booking={booking}
          compliance={compliance}
          setCompliance={setCompliance}
          onSaveCompliance={handleSaveCompliance}
          savingCompliance={savingCompliance}
          checkingIn={checkingIn}
          checkingOut={checkingOut}
          onCheckIn={handleCheckIn}
          onCheckOut={handleCheckOut}
        />
      )}
    </AppLayout>
  )
}
