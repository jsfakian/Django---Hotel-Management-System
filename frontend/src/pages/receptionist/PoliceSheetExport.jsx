import React, { useState } from 'react'
import {
  Alert, Box, Button, Card, CardContent, Grid, TextField, Typography,
} from '@mui/material'
import { Download } from '@mui/icons-material'
import { downloadFile } from '../../services/downloadFile'

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

function buildUrl({ propertyId, dateFrom, dateTo, format }) {
  const q = new URLSearchParams({
    property_id: String(propertyId),
    format,
  })
  if (dateFrom) q.set('date_from', dateFrom)
  if (dateTo) q.set('date_to', dateTo)
  return `/compliance/police-sheet/?${q.toString()}`
}

export default function PoliceSheetExport() {
  const [form, setForm] = useState({
    property_id: '1',
    date_from: todayIso(),
    date_to: todayIso(),
  })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleDownload = async (format) => {
    setError('')
    if (!form.property_id) {
      setError('Property ID is required.')
      return
    }
    setBusy(true)
    try {
      const url = buildUrl({
        propertyId: form.property_id,
        dateFrom: form.date_from,
        dateTo: form.date_to,
        format,
      })
      const stamp = todayIso().replace(/-/g, '')
      await downloadFile(url, `police_sheet_${form.property_id}_${stamp}.${format}`)
    } catch {
      setError('Export failed. Check property ID and permissions.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>
          Police / ΣΑΕ sheet export
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Download guest registration rows for a property and arrival window.
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              required
              label="Property ID"
              type="number"
              value={form.property_id}
              onChange={set('property_id')}
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              fullWidth
              size="small"
              type="date"
              label="From"
              InputLabelProps={{ shrink: true }}
              value={form.date_from}
              onChange={set('date_from')}
            />
          </Grid>
          <Grid item xs={6} sm={3}>
            <TextField
              fullWidth
              size="small"
              type="date"
              label="To"
              InputLabelProps={{ shrink: true }}
              value={form.date_to}
              onChange={set('date_to')}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                size="small"
                variant="outlined"
                startIcon={<Download />}
                disabled={busy}
                onClick={() => handleDownload('csv')}
              >
                CSV
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<Download />}
                disabled={busy}
                onClick={() => handleDownload('xml')}
              >
                XML
              </Button>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  )
}
