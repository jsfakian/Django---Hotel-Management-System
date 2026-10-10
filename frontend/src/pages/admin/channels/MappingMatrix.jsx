import React, { useMemo, useState } from 'react'
import {
  Alert, Box, Button, Stack, TextField, Typography, Chip,
} from '@mui/material'

function rowsFromConfig(mappingConfig) {
  const rooms = mappingConfig?.room_type_mappings
    || mappingConfig?.room_mappings
    || mappingConfig?.rooms
    || {}
  const rates = mappingConfig?.rate_plan_mappings
    || mappingConfig?.rate_mappings
    || mappingConfig?.rates
    || {}
  const roomKeys = Object.keys(rooms)
  const rateKeys = Object.keys(rates)
  const keys = Array.from(new Set([...roomKeys, ...rateKeys]))
  if (!keys.length) {
    return [{ local_room_type_id: '', ota_room_id: '', local_rate_plan_id: '', ota_rate_id: '' }]
  }
  return keys.map((k) => ({
    local_room_type_id: roomKeys.includes(k) ? k : '',
    ota_room_id: roomKeys.includes(k) ? String(rooms[k] ?? '') : '',
    local_rate_plan_id: rateKeys.includes(k) ? k : '',
    ota_rate_id: rateKeys.includes(k) ? String(rates[k] ?? '') : '',
  }))
}

function configFromRows(rows) {
  const room_mappings = {}
  const rate_mappings = {}
  rows.forEach((r) => {
    if (r.local_room_type_id && r.ota_room_id) {
      room_mappings[String(r.local_room_type_id)] = String(r.ota_room_id)
    }
    if (r.local_rate_plan_id && r.ota_rate_id) {
      rate_mappings[String(r.local_rate_plan_id)] = String(r.ota_rate_id)
    }
  })
  // Dual keys for backend normalize_mapping_config compatibility
  return {
    room_mappings,
    room_type_mappings: { ...room_mappings },
    rate_mappings,
    rate_plan_mappings: { ...rate_mappings },
  }
}

export default function MappingMatrix({
  mappingConfigText,
  onMappingConfigChange,
  onValidate,
  validating,
  validation,
}) {
  const initial = useMemo(() => {
    try {
      return rowsFromConfig(JSON.parse(mappingConfigText || '{}'))
    } catch {
      return [{ local_room_type_id: '', ota_room_id: '', local_rate_plan_id: '', ota_rate_id: '' }]
    }
  }, [mappingConfigText])

  const [rows, setRows] = useState(initial)

  const syncJson = (nextRows) => {
    setRows(nextRows)
    onMappingConfigChange(JSON.stringify(configFromRows(nextRows), null, 2))
  }

  const setCell = (idx, key, value) => {
    const next = rows.map((r, i) => (i === idx ? { ...r, [key]: value } : r))
    syncJson(next)
  }

  const errors = validation?.errors || validation?.mapping_errors || []
  const ok = validation && !errors.length && (validation.valid === true || validation.ok === true)

  return (
    <Box>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        Room type × rate plan mapping
      </Typography>
      <Stack spacing={1.5}>
        {rows.map((row, idx) => (
          <Stack key={idx} direction={{ xs: 'column', md: 'row' }} spacing={1}>
            <TextField
              size="small"
              label="Local room type ID"
              value={row.local_room_type_id}
              onChange={(e) => setCell(idx, 'local_room_type_id', e.target.value)}
              fullWidth
            />
            <TextField
              size="small"
              label="OTA room ID"
              value={row.ota_room_id}
              onChange={(e) => setCell(idx, 'ota_room_id', e.target.value)}
              fullWidth
            />
            <TextField
              size="small"
              label="Local rate plan ID"
              value={row.local_rate_plan_id}
              onChange={(e) => setCell(idx, 'local_rate_plan_id', e.target.value)}
              fullWidth
            />
            <TextField
              size="small"
              label="OTA rate ID"
              value={row.ota_rate_id}
              onChange={(e) => setCell(idx, 'ota_rate_id', e.target.value)}
              fullWidth
            />
          </Stack>
        ))}
      </Stack>
      <Stack direction="row" spacing={1} sx={{ mt: 1.5, mb: 1 }} alignItems="center">
        <Button
          size="small"
          onClick={() => syncJson([
            ...rows,
            { local_room_type_id: '', ota_room_id: '', local_rate_plan_id: '', ota_rate_id: '' },
          ])}
        >
          Add row
        </Button>
        {onValidate && (
          <Button size="small" variant="outlined" disabled={validating} onClick={onValidate}>
            Validate mappings
          </Button>
        )}
        {ok && <Chip size="small" color="success" label="Mappings valid" />}
      </Stack>
      {errors.length > 0 && (
        <Alert severity="warning" sx={{ mb: 1 }}>
          {errors.map((e, i) => (
            <Typography key={i} variant="body2">{typeof e === 'string' ? e : (e.message || JSON.stringify(e))}</Typography>
          ))}
        </Alert>
      )}
      <TextField
        fullWidth
        multiline
        minRows={3}
        label="Mapping config (JSON)"
        value={mappingConfigText}
        onChange={(e) => {
          onMappingConfigChange(e.target.value)
          try {
            setRows(rowsFromConfig(JSON.parse(e.target.value || '{}')))
          } catch {
            /* keep matrix until JSON is valid again */
          }
        }}
        helperText='Matrix edits write room_type_mappings + room_mappings and rate_plan_mappings + rate_mappings'
      />
    </Box>
  )
}
