import React, { useMemo, useState } from 'react'
import {
  Box, Button, TextField, Typography, Paper, Table, TableHead, TableBody, TableRow, TableCell,
  Chip, Tooltip, MenuItem, Alert,
} from '@mui/material'
import AppLayout from '../../components/layout/AppLayout'
import ErrorAlert from '../../components/common/ErrorAlert'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import {
  useAssignRoomMutation,
  useGetTapeChartQuery,
} from '../../features/front-desk/frontDeskApi'

function isoToday() {
  return new Date().toISOString().slice(0, 10)
}

function isoPlus(days) {
  const d = new Date()
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

function buildDates(from, to) {
  const out = []
  const cur = new Date(`${from}T00:00:00`)
  const end = new Date(`${to}T00:00:00`)
  while (cur < end) {
    out.push(cur.toISOString().slice(0, 10))
    cur.setDate(cur.getDate() + 1)
  }
  return out
}

function BookingChip({ booking }) {
  if (!booking) return null
  const label = booking.guest_name || booking.guest || booking.status || 'Stay'
  return (
    <Tooltip title={`${label} (${booking.status || ''}) #${booking.booking_id || booking.id || ''}`}>
      <Chip size="small" color="primary" label={label} sx={{ maxWidth: 120 }} />
    </Tooltip>
  )
}

function TapeTable({ rooms, dates, onDropAssign, selectedBookingId }) {
  return (
    <Paper sx={{ overflow: 'auto' }}>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell sx={{ minWidth: 100 }}>Room</TableCell>
            {dates.map((d) => (
              <TableCell key={d} align="center" sx={{ minWidth: 88 }}>{d.slice(5)}</TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {rooms.map((room) => (
            <TableRow key={room.room_id || room.id || room.room_number}>
              <TableCell
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault()
                  const bookingId = e.dataTransfer.getData('text/booking-id') || selectedBookingId
                  if (bookingId) onDropAssign(bookingId, room.room_id || room.id)
                }}
                sx={{ cursor: 'copy' }}
              >
                <Typography variant="body2" fontWeight={600}>{room.room_number}</Typography>
                <Typography variant="caption" color="text.secondary">{room.status}</Typography>
              </TableCell>
              {(room.cells || dates.map((d) => ({ date: d }))).map((cell) => {
                const d = cell.date
                const booking = cell.booking_id
                  ? { booking_id: cell.booking_id, guest: cell.guest, status: cell.status }
                  : null
                return (
                  <TableCell
                    key={d}
                    align="center"
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault()
                      const bookingId = e.dataTransfer.getData('text/booking-id') || selectedBookingId
                      if (bookingId) onDropAssign(bookingId, room.room_id || room.id)
                    }}
                    sx={{ bgcolor: booking ? 'rgba(11,95,107,0.12)' : 'transparent' }}
                  >
                    <BookingChip booking={booking} />
                  </TableCell>
                )
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Paper>
  )
}

export default function TapeChartPage() {
  const [propertyId, setPropertyId] = useState('1')
  const [dateFrom, setDateFrom] = useState(isoToday())
  const [dateTo, setDateTo] = useState(isoPlus(7))
  const [selectedBookingId, setSelectedBookingId] = useState('')
  const [message, setMessage] = useState('')

  const { data, isLoading, error, refetch } = useGetTapeChartQuery({
    property_id: propertyId || undefined,
    date_from: dateFrom,
    date_to: dateTo,
  })
  const [assignRoom, { isLoading: assigning }] = useAssignRoomMutation()

  const rooms = data?.rooms || []
  const unassigned = data?.unassigned || []
  const dates = useMemo(() => buildDates(dateFrom, dateTo), [dateFrom, dateTo])

  const handleAssign = async (bookingId, roomId) => {
    setMessage('')
    try {
      await assignRoom({ bookingId, room_id: roomId }).unwrap()
      setMessage(`Assigned booking #${bookingId} → room ${roomId}`)
      setSelectedBookingId('')
      refetch()
    } catch (err) {
      setMessage(err?.data?.error || err?.data?.detail || 'Assign failed')
    }
  }

  return (
    <AppLayout>
      <Typography variant="h5" sx={{ mb: 1, fontFamily: '"Fraunces", Georgia, serif' }}>Tape chart</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Drag an unassigned booking onto a room row (or select + Assign) to place it.
      </Typography>

      <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
        <TextField size="small" label="Property ID" type="number" value={propertyId} onChange={(e) => setPropertyId(e.target.value)} />
        <TextField size="small" type="date" label="From" InputLabelProps={{ shrink: true }} value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        <TextField size="small" type="date" label="To" InputLabelProps={{ shrink: true }} value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
      </Box>

      {error && <ErrorAlert error={error} />}
      {message && <Alert severity="info" sx={{ mb: 2 }}>{message}</Alert>}

      {unassigned.length > 0 && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>Unassigned room-type bookings</Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
            {unassigned.map((b) => (
              <Chip
                key={b.booking_id}
                draggable
                onDragStart={(e) => {
                  e.dataTransfer.setData('text/booking-id', String(b.booking_id))
                  setSelectedBookingId(String(b.booking_id))
                }}
                onClick={() => setSelectedBookingId(String(b.booking_id))}
                color={String(selectedBookingId) === String(b.booking_id) ? 'primary' : 'default'}
                label={`#${b.booking_id} ${b.guest || ''} ${b.check_in}→${b.check_out}`}
                sx={{ cursor: 'grab' }}
              />
            ))}
            <TextField
              select
              size="small"
              label="Assign to room"
              sx={{ minWidth: 140 }}
              value=""
              disabled={!selectedBookingId || assigning}
              onChange={(e) => handleAssign(selectedBookingId, e.target.value)}
            >
              {rooms.map((r) => (
                <MenuItem key={r.room_id} value={r.room_id}>{r.room_number}</MenuItem>
              ))}
            </TextField>
            {selectedBookingId && (
              <Button size="small" onClick={() => setSelectedBookingId('')}>Clear</Button>
            )}
          </Box>
        </Paper>
      )}

      {isLoading && <LoadingSpinner />}
      {!isLoading && !error && rooms.length === 0 && (
        <Typography color="text.secondary">No tape-chart data for this range.</Typography>
      )}
      {!isLoading && rooms.length > 0 && (
        <TapeTable
          rooms={rooms}
          dates={dates}
          selectedBookingId={selectedBookingId}
          onDropAssign={handleAssign}
        />
      )}
    </AppLayout>
  )
}
