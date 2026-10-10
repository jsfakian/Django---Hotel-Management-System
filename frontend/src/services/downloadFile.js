import axiosInstance from './axiosInstance'

/** Site origin (strip /api/v1) for legacy PDF routes outside the REST prefix. */
export function siteOrigin() {
  const base = import.meta.env.VITE_API_BASE_URL || ''
  const stripped = base.replace(/\/api\/v1\/?$/, '')
  return stripped || window.location.origin
}

export async function downloadFile(url, filename) {
  const response = await axiosInstance.get(url, { responseType: 'blob' })
  const href = URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = href
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(href)
}
