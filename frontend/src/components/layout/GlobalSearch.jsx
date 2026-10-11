import React, { useDeferredValue, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import {
  Autocomplete,
  TextField,
  CircularProgress,
  Box,
  Typography,
} from '@mui/material'
import { Search } from '@mui/icons-material'
import { useGetGuestsQuery } from '../../features/guests/guestsApi'
import { useGetBookingsQuery } from '../../features/bookings/bookingsApi'
import { selectUserRole } from '../../features/auth/authSlice'

function guestPath(role, id) {
  if (role === 'receptionist') return `/receptionist/guests`
  if (role === 'manager') return `/admin/guests/${id}`
  return `/admin/guests/${id}`
}

function bookingPath(role, id) {
  if (role === 'receptionist') return `/receptionist/bookings`
  if (role === 'manager') return `/manager/bookings`
  return `/admin/bookings/${id}`
}

export default function GlobalSearch() {
  const navigate = useNavigate()
  const role = useSelector(selectUserRole)
  const [input, setInput] = useState('')
  const deferred = useDeferredValue(input.trim())
  const enabled = deferred.length >= 2

  const { data: guestsData, isFetching: guestsLoading } = useGetGuestsQuery(
    { search: deferred },
    { skip: !enabled },
  )
  const { data: bookingsData, isFetching: bookingsLoading } = useGetBookingsQuery(
    { search: deferred },
    { skip: !enabled },
  )

  const guests = (guestsData?.results || guestsData || []).slice(0, 5)
  const bookings = (bookingsData?.results || bookingsData || []).slice(0, 5)

  const options = [
    ...guests.map((g) => ({
      key: `g-${g.id}`,
      kind: 'Guest',
      label: g.full_name || g.name || `${g.first_name || ''} ${g.last_name || ''}`.trim() || g.email || `Guest #${g.id}`,
      sub: g.email || g.phone || '',
      path: guestPath(role, g.id),
    })),
    ...bookings.map((b) => ({
      key: `b-${b.id}`,
      kind: 'Booking',
      label: `#${b.id}${b.guest_name ? ` · ${b.guest_name}` : ''}`,
      sub: [b.status, b.check_in, b.check_out].filter(Boolean).join(' · '),
      path: bookingPath(role, b.id),
    })),
  ]

  const loading = enabled && (guestsLoading || bookingsLoading)

  if (role === 'guest' || role === 'staff') return null

  return (
    <Autocomplete
      size="small"
      sx={{ width: { xs: 140, sm: 240, md: 280 }, mr: 1 }}
      options={options}
      filterOptions={(x) => x}
      getOptionLabel={(o) => o.label || ''}
      isOptionEqualToValue={(a, b) => a.key === b.key}
      loading={loading}
      inputValue={input}
      onInputChange={(_, v) => setInput(v)}
      onChange={(_, opt) => {
        if (opt?.path) {
          navigate(opt.path)
          setInput('')
        }
      }}
      noOptionsText={enabled ? 'No matches' : 'Type to search'}
      renderOption={(props, option) => (
        <Box component="li" {...props} key={option.key}>
          <Box>
            <Typography variant="body2" fontWeight={600}>{option.label}</Typography>
            <Typography variant="caption" color="text.secondary">
              {option.kind}{option.sub ? ` · ${option.sub}` : ''}
            </Typography>
          </Box>
        </Box>
      )}
      renderInput={(params) => (
        <TextField
          {...params}
          placeholder="Search guests or bookings"
          InputProps={{
            ...params.InputProps,
            startAdornment: (
              <>
                <Search fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
                {params.InputProps.startAdornment}
              </>
            ),
            endAdornment: (
              <>
                {loading ? <CircularProgress color="inherit" size={16} /> : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
    />
  )
}
