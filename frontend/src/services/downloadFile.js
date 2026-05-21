import axiosInstance from './axiosInstance'

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
