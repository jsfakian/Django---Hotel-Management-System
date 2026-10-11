const STORAGE_KEY = 'nephele.navPins'

export function loadPins(role) {
  try {
    const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
    return Array.isArray(raw[role]) ? raw[role] : []
  } catch {
    return []
  }
}

export function savePins(role, paths) {
  try {
    const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
    raw[role] = paths.slice(0, 5)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(raw))
  } catch {
    // ignore quota / private mode
  }
}

export function togglePin(role, path) {
  const current = loadPins(role)
  const next = current.includes(path)
    ? current.filter((p) => p !== path)
    : [...current, path].slice(0, 5)
  savePins(role, next)
  return next
}
