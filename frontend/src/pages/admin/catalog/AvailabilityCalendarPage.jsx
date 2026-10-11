import React, { useMemo, useState } from 'react'
import {
  Box, Button, FormControl, FormControlLabel, InputLabel, MenuItem, Select,
  TextField, Typography, Table, TableHead, TableBody, TableRow, TableCell,
  Paper, Switch, Alert,
} from '@mui/material'
import PageShell from '../../../components/common/PageShell'
import ErrorAlert from '../../../components/common/ErrorAlert'
import {
  useGetRoomTypesQuery,
  useLazyGetRoomTypeAvailabilityQuery,
  usePatchRoomTypeAvailabilityMutation,
} from '../../../features/catalog/catalogApi'

function dateRange(from, to) {
  if (!from || !to || to <= from) return []
  const days = []
  const cur = new Date(`${from}T00:00:00`)
  const end = new Date(`${to}T00:00:00`)
  while (cur < end) {
    days.push(cur.toISOString().slice(0, 10))
    cur.setDate(cur.getDate() + 1)
  }
  return days
}

function defaultAllotment(roomType) {
  if (roomType?.physical_room_count != null) return Number(roomType.physical_room_count)
  if (roomType?.capacity != null) return Number(roomType.capacity)
  return 1
}

function emptyDay(allotment) {
  return { allotment, min_stay: 1, stop_sell: false }
}

function buildDayState(dates, apiRows, allotmentDefault) {
  const byDate = {}
  ;(apiRows || []).forEach((row) => {
    const d = String(row.date || '').slice(0, 10)
    if (!d) return
    byDate[d] = {
      allotment: row.allotment ?? allotmentDefault,
      min_stay: row.min_stay ?? 1,
      stop_sell: Boolean(row.stop_sell),
    }
  })
  const state = {}
  dates.forEach((d) => {
    state[d] = byDate[d] || emptyDay(allotmentDefault)
  })
  return state
}

function CalendarGrid({ dates, dayState, setDayState }) {
  const update = (date, key, value) => {
    setDayState((prev) => ({
      ...prev,
      [date]: { ...prev[date], [key]: value },
    }))
  }

  return (
    <Paper sx={{ overflow: 'auto' }}>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            <TableCell>Date</TableCell>
            <TableCell>Allotment</TableCell>
            <TableCell>Min stay</TableCell>
            <TableCell>Stop sell</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {dates.map((d) => {
            const row = dayState[d] || emptyDay(1)
            return (
              <TableRow key={d}>
                <TableCell>{d}</TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    type="number"
                    value={row.allotment}
                    onChange={(e) => update(d, 'allotment', Number(e.target.value))}
                    sx={{ width: 90 }}
                  />
                </TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    type="number"
                    value={row.min_stay}
                    onChange={(e) => update(d, 'min_stay', Number(e.target.value))}
                    sx={{ width: 90 }}
                  />
                </TableCell>
                <TableCell>
                  <Switch
                    checked={Boolean(row.stop_sell)}
                    onChange={(e) => update(d, 'stop_sell', e.target.checked)}
                  />
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </Paper>
  )
}

function BulkToolbar({ applyBulk }) {
  return (
    <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
      <Button size="small" onClick={() => applyBulk('allotment', 0)}>Allotment 0</Button>
      <Button size="small" onClick={() => applyBulk('allotment', 1)}>Allotment 1</Button>
      <Button size="small" onClick={() => applyBulk('stop_sell', true)}>Stop sell all</Button>
      <Button size="small" onClick={() => applyBulk('stop_sell', false)}>Open all</Button>
    </Box>
  )
}

export default function AvailabilityCalendarPage({ embedded = false }) {
  const today = new Date()
  const defaultFrom = today.toISOString().slice(0, 10)
  const defaultTo = new Date(today.getTime() + 7 * 86400000).toISOString().slice(0, 10)

  const [roomTypeId, setRoomTypeId] = useState('')
  const [dateFrom, setDateFrom] = useState(defaultFrom)
  const [dateTo, setDateTo] = useState(defaultTo)
  const [dayState, setDayState] = useState({})
  const [staffOverride, setStaffOverride] = useState(true)
  const [message, setMessage] = useState(null)
  const [saveError, setSaveError] = useState(null)

  const { data, error } = useGetRoomTypesQuery()
  const [fetchAvailability, { isFetching }] = useLazyGetRoomTypeAvailabilityQuery()
  const [patchAvailability, { isLoading: saving }] = usePatchRoomTypeAvailabilityMutation()
  const roomTypes = data?.results || data || []
  const dates = useMemo(() => dateRange(dateFrom, dateTo), [dateFrom, dateTo])
  const selectedRt = roomTypes.find((rt) => String(rt.id) === String(roomTypeId))

  const loadGrid = async () => {
    setMessage(null)
    setSaveError(null)
    if (!roomTypeId) {
      setSaveError({ data: { detail: 'Select a room type' } })
      return
    }
    const allotmentDefault = defaultAllotment(selectedRt)
    const result = await fetchAvailability({
      id: roomTypeId,
      date_from: dateFrom,
      date_to: dateTo,
    })
    if (result.error) {
      setSaveError(result.error)
      setDayState(buildDayState(dates, [], allotmentDefault))
      return
    }
    const rows = result.data?.results || result.data || []
    setDayState(buildDayState(dates, rows, allotmentDefault))
  }

  const applyBulk = (field, value) => {
    setDayState((prev) => {
      const next = { ...prev }
      dates.forEach((d) => {
        next[d] = { ...(next[d] || emptyDay(1)), [field]: value }
      })
      return next
    })
  }

  const handleSave = async () => {
    setSaveError(null)
    setMessage(null)
    if (!roomTypeId) {
      setSaveError({ data: { detail: 'Select a room type' } })
      return
    }
    const days = dates.map((date) => ({
      date,
      allotment: Number(dayState[date]?.allotment ?? 0),
      min_stay: Number(dayState[date]?.min_stay ?? 1),
      stop_sell: Boolean(dayState[date]?.stop_sell),
      staff_override: staffOverride,
    }))
    const result = await patchAvailability({
      id: roomTypeId,
      date_from: dateFrom,
      date_to: dateTo,
      staff_override: staffOverride,
      days,
    })
    if (result.error) {
      setSaveError(result.error)
    } else {
      setMessage('Availability saved')
    }
  }

  return (
    <PageShell embedded={embedded}>
      {!embedded && (
        <>
          <Typography variant="h5" sx={{ mb: 2, fontFamily: '"Fraunces", Georgia, serif' }}>
            Availability calendar
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Edit allotment, min stay, and stop-sell by room type for a date range.
          </Typography>
        </>
      )}

      {error && <ErrorAlert error={error} />}
      {saveError && <ErrorAlert error={saveError} />}
      {message && <Alert severity="success" sx={{ mb: 2 }}>{message}</Alert>}

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mb: 2, alignItems: 'center' }}>
        <FormControl size="small" sx={{ minWidth: 220 }}>
          <InputLabel>Room type</InputLabel>
          <Select label="Room type" value={roomTypeId} onChange={(e) => setRoomTypeId(e.target.value)}>
            {roomTypes.map((rt) => (
              <MenuItem key={rt.id} value={rt.id}>{rt.code} — {rt.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <TextField size="small" type="date" label="From" InputLabelProps={{ shrink: true }} value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        <TextField size="small" type="date" label="To" InputLabelProps={{ shrink: true }} value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        <FormControlLabel
          control={<Switch checked={staffOverride} onChange={(e) => setStaffOverride(e.target.checked)} />}
          label="Staff override"
        />
        <Button variant="outlined" onClick={loadGrid} disabled={isFetching}>
          {isFetching ? 'Loading…' : 'Load grid'}
        </Button>
        <Button variant="contained" onClick={handleSave} disabled={saving || !dates.length}>Save</Button>
      </Box>

      {dates.length > 0 && Object.keys(dayState).length > 0 && (
        <>
          <BulkToolbar applyBulk={applyBulk} />
          <CalendarGrid dates={dates} dayState={dayState} setDayState={setDayState} />
        </>
      )}
    </PageShell>
  )
}
