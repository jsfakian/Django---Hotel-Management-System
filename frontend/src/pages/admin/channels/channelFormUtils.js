export const EMPTY_CHANNEL_FORM = {
  channel_name: '',
  property: '',
  account_id: '',
  api_key: '',
  api_secret: '',
  mapping_config: '{}',
  is_active: true,
  sync_enabled: true,
}

export function channelLabel(value) {
  return (value || '').replace(/_/g, '.')
}

export function parseMappingConfig(raw) {
  const text = (raw || '{}').trim() || '{}'
  return JSON.parse(text)
}

/**
 * Dual-write canonical + legacy mapping keys for backward-compat API clients.
 * Backend normalize_mapping_config accepts either; this is the ONE place that
 * expands both shapes (MappingMatrix emits canonical keys only).
 */
export function withDualMappingKeys(cfg) {
  const raw = cfg || {}
  const rooms = raw.room_type_mappings || raw.room_mappings || {}
  const rates = raw.rate_plan_mappings || raw.rate_mappings || {}
  const room = Object.fromEntries(
    Object.entries(rooms).map(([k, v]) => [String(k), v]),
  )
  const rate = Object.fromEntries(
    Object.entries(rates).map(([k, v]) => [String(k), v]),
  )
  return {
    ...raw,
    room_mappings: room,
    room_type_mappings: room,
    rate_mappings: rate,
    rate_plan_mappings: rate,
  }
}

export function buildChannelPayload(form) {
  return {
    channel_name: form.channel_name,
    property: Number(form.property),
    account_id: form.account_id,
    api_key: form.api_key || undefined,
    api_secret: form.api_secret || undefined,
    mapping_config: withDualMappingKeys(parseMappingConfig(form.mapping_config)),
    is_active: Boolean(form.is_active),
    sync_enabled: Boolean(form.sync_enabled),
  }
}

export function formFromChannel(row) {
  return {
    channel_name: row.channel_name || '',
    property: row.property || '',
    account_id: row.account_id || '',
    api_key: '',
    api_secret: '',
    mapping_config: JSON.stringify(row.mapping_config || {}, null, 2),
    is_active: row.is_active !== false,
    sync_enabled: row.sync_enabled !== false,
  }
}
