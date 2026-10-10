import React, { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Alert, Box, Button, CircularProgress, Typography, Stack, Divider, Chip,
} from '@mui/material'
import BookingShell from './BookingShell'
import { useBookingT } from './bookingLang'
import { quoteAvailability, saveBookingDraft, loadBookingDraft } from '../../../features/public/publicBookingApi'

function SmartRateBadge({ item }) {
  if (!item?.smart_rate && !item?.smart_rate_label) return null
  const label = item.smart_rate_label || 'Smart rate'
  const hint = item.smart_rate_hint || item.smart_rate_reason || ''
  return (
    <Chip
      size="small"
      color="secondary"
      variant="outlined"
      label={label}
      title={hint || undefined}
      sx={{ mt: 0.5, fontWeight: 600 }}
    />
  )
}

function ResultRow({ item, onSelect, t }) {
  const allotment = item.available_allotment != null ? `${item.available_allotment} ${t('left')}` : ''
  const nights = item.nights ? `${item.nights} ${t('nights')}` : ''
  return (
    <Box
      sx={{
        py: 2,
        display: 'flex',
        flexWrap: 'wrap',
        gap: 2,
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Box>
        <Typography variant="subtitle1" fontWeight={600}>
          {item.room_type_name || item.room_type?.name || 'Room'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {item.rate_plan_name || item.rate_plan?.name || 'Rate'}
          {item.meal_plan ? ` · ${item.meal_plan}` : ''}
          {item.is_refundable === false ? ` · ${t('nonRefundable')}` : ''}
        </Typography>
        <SmartRateBadge item={item} />
        <Typography variant="caption" color="text.secondary" display="block">
          {[allotment, nights].filter(Boolean).join(' · ')}
        </Typography>
      </Box>
      <Stack direction="row" spacing={2} alignItems="center">
        <Typography variant="h6" sx={{ fontFamily: '"Fraunces", Georgia, serif' }}>
          €{Number(item.total || 0).toFixed(2)}
        </Typography>
        <Button variant="contained" color="secondary" onClick={() => onSelect(item)}>
          {t('select')}
        </Button>
      </Stack>
    </Box>
  )
}

function ResultsBody() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const { t } = useBookingT()
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const propertyId = Number(params.get('property_id'))
  const checkIn = params.get('check_in')
  const checkOut = params.get('check_out')
  const adults = Number(params.get('adults') || 1)
  const children = Number(params.get('children') || 0)
  const search = { property_id: propertyId, check_in: checkIn, check_out: checkOut, adults, children }

  useEffect(() => {
    let cancelled = false
    async function run() {
      setLoading(true)
      setError('')
      try {
        if (!propertyId || !checkIn || !checkOut) {
          throw new Error(t('missingSearch'))
        }
        const data = await quoteAvailability({
          property_id: propertyId,
          check_in: checkIn,
          check_out: checkOut,
          adults,
          children,
        })
        const list = Array.isArray(data) ? data : (data?.results || data?.products || [])
        if (!cancelled) setResults(list)
      } catch (err) {
        if (!cancelled) setError(err.message || t('loadAvailabilityFail'))
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [propertyId, checkIn, checkOut, adults, children, t])

  const handleSelect = (item) => {
    const prev = loadBookingDraft() || {}
    saveBookingDraft({
      ...prev,
      ...search,
      room_type_id: item.room_type_id || item.room_type?.id,
      rate_plan_id: item.rate_plan_id || item.rate_plan?.id,
      room_type_name: item.room_type_name,
      rate_plan_name: item.rate_plan_name,
      total: item.total,
      currency: item.currency || 'EUR',
      nightly_prices: item.nightly_prices,
    })
    navigate('/book/guest')
  }

  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6" sx={{ fontFamily: '"Fraunces", Georgia, serif' }}>{t('availableRates')}</Typography>
        <Button onClick={() => navigate('/book')}>{t('editSearch')}</Button>
      </Box>
      <Divider sx={{ mb: 1 }} />
      {loading && <Box sx={{ py: 4, textAlign: 'center' }}><CircularProgress /></Box>}
      {error && <Alert severity="error">{error}</Alert>}
      {!loading && !error && results.length === 0 && (
        <Alert severity="info">{t('noAvailability')}</Alert>
      )}
      {results.map((item, idx) => (
        <ResultRow key={`${item.room_type_id}-${item.rate_plan_id}-${idx}`} item={item} onSelect={handleSelect} t={t} />
      ))}
    </>
  )
}

export default function BookingResultsPage() {
  const [params] = useSearchParams()
  const checkIn = params.get('check_in') || '—'
  const checkOut = params.get('check_out') || '—'
  const adults = params.get('adults') || '1'
  return (
    <BookingShell subtitle={`${checkIn} → ${checkOut} · ${adults}`}>
      <ResultsBody />
    </BookingShell>
  )
}
