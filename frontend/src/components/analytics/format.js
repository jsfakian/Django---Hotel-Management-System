export const PERIODS = [
  ['day', 'Today'], ['week', 'Last 7 days'], ['month', 'Last 30 days'], ['year', 'Last 12 months'],
]

export const num = (v) => Number(v || 0)
export const euro = (v, digits = 0) =>
  `€${num(v).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits })}`
export const pct = (v, digits = 1) => `${num(v).toFixed(digits)}%`

export const periodLabel = (data) => (data?.from_date ? `${data.from_date} → ${data.to_date}` : '')
